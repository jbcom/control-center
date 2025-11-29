"""AWS Connector using jbcom ecosystem packages."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Optional

import boto3
from boto3.resources.base import ServiceResource
from botocore.config import Config
from botocore.exceptions import ClientError
from deepmerge import always_merger
from directed_inputs_class import DirectedInputsClass
from extended_data_types import is_nothing, unhump_map
from lifecyclelogging import Logging

if TYPE_CHECKING:
    pass


class AWSConnector(DirectedInputsClass):
    """AWS connector for boto3 client and resource management."""

    def __init__(
        self,
        execution_role_arn: Optional[str] = None,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.execution_role_arn = execution_role_arn
        self.aws_sessions: dict[str, dict[str, boto3.Session]] = {}
        self.default_aws_session = boto3.Session()
        self.logging = logger or Logging(logger_name="AWSConnector")
        self.logger = self.logging.logger

    def assume_role(self, execution_role_arn: str, role_session_name: str) -> boto3.Session:
        """Assume an AWS IAM role and return a boto3 Session."""
        self.logger.info(f"Attempting to assume role: {execution_role_arn}")
        sts_client = self.default_aws_session.client("sts")

        try:
            response = sts_client.assume_role(RoleArn=execution_role_arn, RoleSessionName=role_session_name)
            credentials = response["Credentials"]
            self.logger.info(f"Successfully assumed role: {execution_role_arn}")
            return boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )
        except ClientError as e:
            self.logger.error(f"Failed to assume role: {execution_role_arn}", exc_info=True)
            raise RuntimeError(f"Failed to assume role {execution_role_arn}") from e

    def get_aws_session(
        self,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
    ) -> boto3.Session:
        """Get a boto3 Session for the specified role."""
        if not execution_role_arn:
            return self.default_aws_session

        if execution_role_arn not in self.aws_sessions:
            self.aws_sessions[execution_role_arn] = {}

        if not role_session_name:
            role_session_name = "VendorConnectors"

        if role_session_name not in self.aws_sessions[execution_role_arn]:
            self.aws_sessions[execution_role_arn][role_session_name] = self.assume_role(
                execution_role_arn, role_session_name
            )

        return self.aws_sessions[execution_role_arn][role_session_name]

    @staticmethod
    def create_standard_retry_config(max_attempts: int = 5) -> Config:
        """Create a standard retry configuration."""
        return Config(retries={"max_attempts": max_attempts, "mode": "standard"})

    def get_aws_client(
        self,
        client_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[Config] = None,
        **client_args,
    ) -> boto3.client:
        """Get a boto3 client for the specified service."""
        session = self.get_aws_session(execution_role_arn, role_session_name)
        if config is None:
            config = self.create_standard_retry_config()
        return session.client(client_name, config=config, **client_args)

    def get_aws_resource(
        self,
        service_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[Config] = None,
        **resource_args,
    ) -> ServiceResource:
        """Get a boto3 resource for the specified service."""
        session = self.get_aws_session(execution_role_arn, role_session_name)
        if config is None:
            config = self.create_standard_retry_config()

        try:
            return session.resource(service_name, config=config, **resource_args)
        except ClientError as e:
            self.logger.error(f"Failed to create resource for service: {service_name}", exc_info=True)
            raise RuntimeError(f"Failed to create resource for service {service_name}") from e

    def get_secret(
        self,
        secret_id: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        secretsmanager: Optional[boto3.client] = None,
    ) -> Optional[str]:
        """Get a single secret value from AWS Secrets Manager.

        Handles both SecretString and SecretBinary responses.

        Args:
            secret_id: The ARN or name of the secret to retrieve.
            execution_role_arn: ARN of role to assume for cross-account access.
            role_session_name: Session name for assumed role.
            secretsmanager: Optional pre-existing Secrets Manager client.

        Returns:
            The secret value as a string, or None if not found.
        """
        self.logger.debug(f"Getting AWS secret: {secret_id}")

        if execution_role_arn:
            self.logger.debug(f"Using execution role: {execution_role_arn}")

        if secretsmanager is None:
            secretsmanager = self.get_aws_client(
                client_name="secretsmanager",
                execution_role_arn=execution_role_arn or self.execution_role_arn,
                role_session_name=role_session_name,
            )

        try:
            response = secretsmanager.get_secret_value(SecretId=secret_id)
            self.logger.debug(f"Successfully retrieved secret: {secret_id}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceNotFoundException":
                self.logger.warning(f"Secret not found: {secret_id}")
                return None
            self.logger.error(f"Failed to get secret {secret_id}: {e}")
            raise ValueError(f"Failed to get secret for ID '{secret_id}'") from e

        # Handle both SecretString and SecretBinary
        if "SecretString" in response:
            secret = response["SecretString"]
            self.logger.debug("Retrieved secret as string")
        else:
            secret = response["SecretBinary"].decode("utf-8")
            self.logger.debug("Retrieved and decoded binary secret")

        return secret

    def list_secrets(
        self,
        filters: Optional[list[dict]] = None,
        name_prefix: Optional[str] = None,
        get_secret_values: bool = False,
        skip_empty_secrets: bool = False,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
    ) -> dict[str, str | dict]:
        """List secrets from AWS Secrets Manager.

        Args:
            filters: List of filter dicts for list_secrets API (e.g., [{"Key": "description", "Values": ["prod"]}])
            name_prefix: Optional prefix helper for the AWS-provided "name" filter.
            get_secret_values: If True, fetch actual secret values, not just ARNs.
            skip_empty_secrets: If True and get_secret_values is True, skip secrets with empty/null values.
            execution_role_arn: ARN of role to assume for cross-account access.
            role_session_name: Session name for assumed role.

        Returns:
            Dict mapping secret names to either ARNs (if get_secret_values=False) or secret values.

        Raises:
            ValueError: If name_prefix contains path traversal sequences.
        """
        self.logger.info("Listing AWS Secrets Manager secrets")

        # Validate name_prefix to prevent path traversal
        if name_prefix and (".." in name_prefix or "\x00" in name_prefix):
            raise ValueError("name_prefix contains invalid characters")

        if skip_empty_secrets:
            get_secret_values = True
            self.logger.debug("Forced get_secret_values to True due to skip_empty_secrets setting")

        role_arn = execution_role_arn or self.execution_role_arn
        secretsmanager = self.get_aws_client(
            client_name="secretsmanager",
            execution_role_arn=role_arn,
            role_session_name=role_session_name,
        )

        secrets: dict[str, str | dict] = {}
        empty_secret_count = 0
        page_count = 0

        paginator = secretsmanager.get_paginator("list_secrets")

        effective_filters: list[dict] = []
        if filters:
            effective_filters.extend(filters)
        if name_prefix:
            effective_filters.append({"Key": "name", "Values": [name_prefix]})

        paginate_kwargs: dict = {"IncludePlannedDeletion": False}
        if effective_filters:
            paginate_kwargs["Filters"] = effective_filters

        self.logger.debug(f"List secrets parameters: {paginate_kwargs}")

        for page in paginator.paginate(**paginate_kwargs):
            page_count += 1
            page_secrets = page.get("SecretList", [])
            self.logger.info(f"Fetching secrets page {page_count}, found {len(page_secrets)} secrets")

            for secret in page_secrets:
                secret_name = secret["Name"]
                secret_arn = secret["ARN"]
                self.logger.debug(f"Processing secret: {secret_name}")

                if get_secret_values:
                    self.logger.debug(f"Fetching secret data for: {secret_name}")
                    secret_value = self.get_secret(
                        secret_id=secret_arn,
                        execution_role_arn=role_arn,
                        role_session_name=role_session_name,
                        secretsmanager=secretsmanager,
                    )

                    if is_nothing(secret_value) and skip_empty_secrets:
                        self.logger.warning(f"Skipping empty secret: {secret_name} ({secret_arn})")
                        empty_secret_count += 1
                        continue

                    secrets[secret_name] = secret_value
                    self.logger.debug(f"Stored secret data for: {secret_name}")
                else:
                    secrets[secret_name] = secret_arn
                    self.logger.debug(f"Stored secret ARN for: {secret_name}")

        self.logger.info(
            f"Secret listing complete. Processed {page_count} pages, "
            f"returned {len(secrets)} secrets, skipped {empty_secret_count} empty"
        )
        return secrets

    def copy_secrets_to_s3(
        self,
        secrets: dict[str, str | dict],
        bucket: str,
        key: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
    ) -> str:
        """Copy secrets dictionary to S3 as JSON.

        Args:
            secrets: Dictionary of secrets to upload.
            bucket: S3 bucket name.
            key: S3 object key.
            execution_role_arn: ARN of role to assume for S3 access.
            role_session_name: Session name for assumed role.

        Returns:
            S3 URI of uploaded object.
        """
        import json

        self.logger.info(f"Copying {len(secrets)} secrets to s3://{bucket}/{key}")

        s3_client = self.get_aws_client(
            client_name="s3",
            execution_role_arn=execution_role_arn or self.execution_role_arn,
            role_session_name=role_session_name,
        )

        body = json.dumps(secrets)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )

        s3_uri = f"s3://{bucket}/{key}"
        self.logger.info(f"Uploaded secrets to {s3_uri}")
        return s3_uri

    @staticmethod
    def load_vendors_from_asm(prefix: str = "/vendors/") -> dict[str, str]:
        """Load vendor secrets from AWS Secrets Manager.

        This is used in Lambda environments where vendor credentials are stored
        in ASM under a common prefix (e.g., /vendors/).

        Args:
            prefix: The prefix path for vendor secrets (default: /vendors/)

        Returns:
            Dictionary mapping secret keys (with prefix removed) to their values.
        """
        import os

        vendors: dict[str, str] = {}
        prefix = os.getenv("TM_VENDORS_PREFIX", prefix)

        try:
            session = boto3.Session()
            secretsmanager = session.client("secretsmanager")

            # List secrets with the prefix
            paginator = secretsmanager.get_paginator("list_secrets")
            for page in paginator.paginate(Filters=[{"Key": "name", "Values": [prefix]}]):
                for secret in page.get("SecretList", []):
                    secret_name = secret["Name"]
                    if secret_name.startswith(prefix):
                        try:
                            response = secretsmanager.get_secret_value(SecretId=secret_name)
                            secret_value = response.get("SecretString", "")
                            # Remove prefix from key name
                            key = secret_name.removeprefix(prefix).upper()
                            vendors[key] = secret_value
                        except ClientError:
                            # Skip secrets we can't read
                            pass
        except ClientError:
            # Return empty dict if we can't access Secrets Manager
            pass

        return vendors

    # =========================================================================
    # AWS Organizations Operations
    # =========================================================================

    def get_organization_accounts(
        self,
        unhump_accounts: bool = True,
        sort_by_name: bool = False,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all AWS accounts from AWS Organizations.

        Recursively traverses the organization hierarchy to get all accounts
        with their organizational unit information and tags.

        Args:
            unhump_accounts: Convert keys to snake_case. Defaults to True.
            sort_by_name: Sort accounts by name. Defaults to False.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping account IDs to account data including:
            - Name, Email, Status, JoinedTimestamp
            - OuId, OuArn, OuName (organizational unit info)
            - tags (account tags)
            - managed (always False for org accounts)

        Raises:
            RuntimeError: If unable to find root parent ID.
        """
        self.logger.info("Getting AWS organization accounts")

        org_units: dict[str, dict[str, Any]] = {}

        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=execution_role_arn or self.execution_role_arn,
        )

        self.logger.info("Getting root information")
        roots = orgs.list_roots()

        try:
            root_parent_id = roots["Roots"][0]["Id"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Failed to find root parent ID: {roots}") from exc

        self.logger.info(f"Root parent ID: {root_parent_id}")

        accounts_paginator = orgs.get_paginator("list_accounts_for_parent")
        ou_paginator = orgs.get_paginator("list_organizational_units_for_parent")
        tags_paginator = orgs.get_paginator("list_tags_for_resource")

        def yield_tag_keypairs(tags: list[dict[str, str]]):
            for tag in tags:
                yield tag["Key"], tag["Value"]

        def get_accounts_recursive(parent_id: str) -> dict[str, dict[str, Any]]:
            accounts: dict[str, dict[str, Any]] = {}

            for page in accounts_paginator.paginate(ParentId=parent_id):
                for account in page["Accounts"]:
                    account_id = account["Id"]
                    account_tags: dict[str, str] = {}
                    for tags_page in tags_paginator.paginate(ResourceId=account_id):
                        for k, v in yield_tag_keypairs(tags_page["Tags"]):
                            account_tags[k] = v

                    account["tags"] = account_tags
                    accounts[account_id] = account

            for page in ou_paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    ou_id = ou["Id"]
                    ou_data = org_units.get(ou_id)
                    if is_nothing(ou_data):
                        ou_data = {}
                        for k, v in deepcopy(ou).items():
                            ou_data[f"Ou{k.title()}"] = v
                        org_units[ou_id] = ou_data

                    for account_id, account_data in get_accounts_recursive(ou_id).items():
                        accounts[account_id] = always_merger.merge(
                            deepcopy(account_data), deepcopy(ou_data)
                        )

            return accounts

        aws_accounts = get_accounts_recursive(root_parent_id)

        self.logger.info("Setting organization accounts initially to unmanaged")
        for account_id in list(aws_accounts.keys()):
            aws_accounts[account_id]["managed"] = False

        # Apply transformations
        if unhump_accounts:
            aws_accounts = {k: unhump_map(v) for k, v in aws_accounts.items()}

        if sort_by_name:
            key_field = "name" if unhump_accounts else "Name"
            aws_accounts = dict(
                sorted(aws_accounts.items(), key=lambda x: x[1].get(key_field, ""))
            )

        self.logger.info(f"Retrieved {len(aws_accounts)} organization accounts")
        return aws_accounts

    def get_controltower_accounts(
        self,
        unhump_accounts: bool = True,
        sort_by_name: bool = False,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all AWS accounts managed by AWS Control Tower.

        Retrieves accounts from the Control Tower Account Factory, which are
        accounts that were provisioned through Control Tower.

        Args:
            unhump_accounts: Convert keys to snake_case. Defaults to True.
            sort_by_name: Sort accounts by name. Defaults to False.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping account IDs to account data including:
            - Name, Email, Status
            - Control Tower specific metadata
            - managed (always True for Control Tower accounts)
        """
        self.logger.info("Getting AWS Control Tower accounts")

        controltower = self.get_aws_client(
            client_name="controltower",
            execution_role_arn=execution_role_arn or self.execution_role_arn,
        )

        accounts: dict[str, dict[str, Any]] = {}
        paginator = controltower.get_paginator("list_enabled_controls")

        # Control Tower uses Service Catalog for account provisioning
        servicecatalog = self.get_aws_client(
            client_name="servicecatalog",
            execution_role_arn=execution_role_arn or self.execution_role_arn,
        )

        try:
            # List provisioned products from Account Factory
            sc_paginator = servicecatalog.get_paginator("search_provisioned_products")
            for page in sc_paginator.paginate(
                Filters={"SearchQuery": ["productType:CONTROL_TOWER_ACCOUNT"]}
            ):
                for product in page.get("ProvisionedProducts", []):
                    # Extract account info from provisioned product
                    account_data = {
                        "Name": product.get("Name", ""),
                        "Status": product.get("Status", ""),
                        "managed": True,
                        "ProvisionedProductId": product.get("Id"),
                        "ProvisionedProductName": product.get("Name"),
                    }

                    # Try to get the account ID from outputs
                    if product.get("Id"):
                        try:
                            outputs = servicecatalog.get_provisioned_product_outputs(
                                ProvisionedProductId=product["Id"]
                            )
                            for output in outputs.get("Outputs", []):
                                if output.get("OutputKey") == "AccountId":
                                    account_id = output.get("OutputValue")
                                    if account_id:
                                        accounts[account_id] = account_data
                                        break
                        except ClientError:
                            pass

        except ClientError as e:
            self.logger.warning(f"Could not list Control Tower accounts: {e}")
            # Fall back to listing from organizations with Control Tower tag
            pass

        # Apply transformations
        if unhump_accounts:
            accounts = {k: unhump_map(v) for k, v in accounts.items()}

        if sort_by_name:
            key_field = "name" if unhump_accounts else "Name"
            accounts = dict(
                sorted(accounts.items(), key=lambda x: x[1].get(key_field, ""))
            )

        self.logger.info(f"Retrieved {len(accounts)} Control Tower accounts")
        return accounts

    def get_accounts(
        self,
        unhump_accounts: bool = True,
        sort_by_name: bool = False,
        include_controltower: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all AWS accounts from Organizations and Control Tower.

        Combines accounts from AWS Organizations and Control Tower, marking
        Control Tower accounts as 'managed'.

        Args:
            unhump_accounts: Convert keys to snake_case. Defaults to True.
            sort_by_name: Sort accounts by name. Defaults to False.
            include_controltower: Include Control Tower accounts. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping account IDs to account data with 'managed' flag
            indicating whether the account is managed by Control Tower.
        """
        self.logger.info("Getting all AWS accounts")

        # Get organization accounts (all marked as unmanaged initially)
        aws_accounts = self.get_organization_accounts(
            unhump_accounts=False,
            sort_by_name=False,
            execution_role_arn=execution_role_arn,
        )

        # Merge with Control Tower accounts if requested
        if include_controltower:
            controltower_accounts = self.get_controltower_accounts(
                unhump_accounts=False,
                sort_by_name=False,
                execution_role_arn=execution_role_arn,
            )

            # Merge - Control Tower accounts override org accounts
            aws_accounts = always_merger.merge(aws_accounts, controltower_accounts)

        # Apply transformations
        if unhump_accounts:
            aws_accounts = {k: unhump_map(v) for k, v in aws_accounts.items()}

        if sort_by_name:
            key_field = "name" if unhump_accounts else "Name"
            aws_accounts = dict(
                sorted(aws_accounts.items(), key=lambda x: x[1].get(key_field, ""))
            )

        self.logger.info(f"Retrieved {len(aws_accounts)} total AWS accounts")
        return aws_accounts

    def get_caller_account_id(self) -> str:
        """Get the AWS account ID of the caller.

        Returns:
            The 12-digit AWS account ID.
        """
        sts = self.get_aws_client("sts")
        identity = sts.get_caller_identity()
        return identity["Account"]

    def get_identity_store_id(
        self,
        execution_role_arn: Optional[str] = None,
    ) -> str:
        """Get the Identity Store ID for AWS IAM Identity Center.

        Args:
            execution_role_arn: ARN of role to assume for access.

        Returns:
            The Identity Store ID.

        Raises:
            RuntimeError: If unable to find Identity Store ID.
        """
        sso_admin = self.get_aws_client(
            client_name="sso-admin",
            execution_role_arn=execution_role_arn or self.execution_role_arn,
        )

        instances = sso_admin.list_instances()
        if not instances.get("Instances"):
            raise RuntimeError("No IAM Identity Center instance found")

        return instances["Instances"][0]["IdentityStoreId"]
