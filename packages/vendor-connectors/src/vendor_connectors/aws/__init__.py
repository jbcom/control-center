"""AWS Connector using jbcom ecosystem packages.

This package provides AWS operations organized into submodules:
- organizations: AWS Organizations and Control Tower account management
- sso: IAM Identity Center (SSO) operations
- s3: S3 bucket and object operations
- secrets: Secrets Manager operations (in base connector)
- ecs: ECS cluster and service operations

Usage:
    from vendor_connectors.aws import AWSConnector

    connector = AWSConnector()
    accounts = connector.get_accounts()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import boto3
from boto3.resources.base import ServiceResource
from botocore.config import Config
from botocore.exceptions import ClientError
from directed_inputs_class import DirectedInputsClass
from extended_data_types import is_nothing
from lifecyclelogging import Logging

if TYPE_CHECKING:
    pass


class AWSConnector(DirectedInputsClass):
    """AWS connector for boto3 client and resource management.

    This is the base connector class providing:
    - Session management and role assumption
    - Client/resource creation with retry configuration
    - Secrets Manager operations

    Higher-level operations are provided via mixin classes from submodules.
    """

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

    # =========================================================================
    # Session Management
    # =========================================================================

    def assume_role(self, execution_role_arn: str, role_session_name: str) -> boto3.Session:
        """Assume an AWS IAM role and return a boto3 Session.

        Args:
            execution_role_arn: ARN of the role to assume.
            role_session_name: Name for the assumed role session.

        Returns:
            A boto3 Session with the assumed role credentials.

        Raises:
            RuntimeError: If role assumption fails.
        """
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
        """Get a boto3 Session, optionally assuming a role.

        Args:
            execution_role_arn: ARN of role to assume. If None, uses default session.
            role_session_name: Name for the assumed role session.

        Returns:
            A boto3 Session.
        """
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

    # =========================================================================
    # Client/Resource Creation
    # =========================================================================

    @staticmethod
    def create_standard_retry_config(max_attempts: int = 5) -> Config:
        """Create a standard retry configuration.

        Args:
            max_attempts: Maximum retry attempts. Defaults to 5.

        Returns:
            A botocore Config with retry settings.
        """
        return Config(retries={"max_attempts": max_attempts, "mode": "standard"})

    def get_aws_client(
        self,
        client_name: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        config: Optional[Config] = None,
        **client_args,
    ) -> boto3.client:
        """Get a boto3 client for the specified service.

        Args:
            client_name: AWS service name (e.g., 's3', 'ec2', 'organizations').
            execution_role_arn: ARN of role to assume for cross-account access.
            role_session_name: Name for the assumed role session.
            config: Optional botocore Config. Defaults to standard retry config.
            **client_args: Additional arguments passed to boto3 client.

        Returns:
            A boto3 client for the specified service.
        """
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
        """Get a boto3 resource for the specified service.

        Args:
            service_name: AWS service name (e.g., 's3', 'ec2', 'dynamodb').
            execution_role_arn: ARN of role to assume for cross-account access.
            role_session_name: Name for the assumed role session.
            config: Optional botocore Config. Defaults to standard retry config.
            **resource_args: Additional arguments passed to boto3 resource.

        Returns:
            A boto3 resource for the specified service.

        Raises:
            RuntimeError: If resource creation fails.
        """
        session = self.get_aws_session(execution_role_arn, role_session_name)
        if config is None:
            config = self.create_standard_retry_config()

        try:
            return session.resource(service_name, config=config, **resource_args)
        except ClientError as e:
            self.logger.error(f"Failed to create resource for service: {service_name}", exc_info=True)
            raise RuntimeError(f"Failed to create resource for service {service_name}") from e

    # =========================================================================
    # Identity Operations
    # =========================================================================

    def get_caller_account_id(self) -> str:
        """Get the AWS account ID of the caller.

        Returns:
            The 12-digit AWS account ID.
        """
        sts = self.get_aws_client("sts")
        identity = sts.get_caller_identity()
        return identity["Account"]

    # =========================================================================
    # Secrets Manager Operations
    # =========================================================================

    def get_secret(
        self,
        secret_id: str,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        secretsmanager: Optional[boto3.client] = None,
    ) -> Optional[str]:
        """Get a single secret value from AWS Secrets Manager.

        Args:
            secret_id: The ARN or name of the secret to retrieve.
            execution_role_arn: ARN of role to assume for cross-account access.
            role_session_name: Session name for assumed role.
            secretsmanager: Optional pre-existing Secrets Manager client.

        Returns:
            The secret value as a string, or None if not found.
        """
        self.logger.debug(f"Getting AWS secret: {secret_id}")

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

        if "SecretString" in response:
            return response["SecretString"]
        else:
            return response["SecretBinary"].decode("utf-8")

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
            filters: List of filter dicts for list_secrets API.
            name_prefix: Optional prefix for the AWS "name" filter.
            get_secret_values: If True, fetch actual secret values.
            skip_empty_secrets: If True, skip secrets with empty values.
            execution_role_arn: ARN of role to assume for cross-account access.
            role_session_name: Session name for assumed role.

        Returns:
            Dict mapping secret names to ARNs or values.

        Raises:
            ValueError: If name_prefix contains invalid characters.
        """
        self.logger.info("Listing AWS Secrets Manager secrets")

        if name_prefix and (".." in name_prefix or "\x00" in name_prefix):
            raise ValueError("name_prefix contains invalid characters")

        if skip_empty_secrets:
            get_secret_values = True

        role_arn = execution_role_arn or self.execution_role_arn
        secretsmanager = self.get_aws_client(
            client_name="secretsmanager",
            execution_role_arn=role_arn,
            role_session_name=role_session_name,
        )

        secrets: dict[str, str | dict] = {}
        paginator = secretsmanager.get_paginator("list_secrets")

        effective_filters: list[dict] = []
        if filters:
            effective_filters.extend(filters)
        if name_prefix:
            effective_filters.append({"Key": "name", "Values": [name_prefix]})

        paginate_kwargs: dict = {"IncludePlannedDeletion": False}
        if effective_filters:
            paginate_kwargs["Filters"] = effective_filters

        for page in paginator.paginate(**paginate_kwargs):
            for secret in page.get("SecretList", []):
                secret_name = secret["Name"]
                secret_arn = secret["ARN"]

                if get_secret_values:
                    secret_value = self.get_secret(
                        secret_id=secret_arn,
                        execution_role_arn=role_arn,
                        role_session_name=role_session_name,
                        secretsmanager=secretsmanager,
                    )

                    if is_nothing(secret_value) and skip_empty_secrets:
                        continue

                    secrets[secret_name] = secret_value
                else:
                    secrets[secret_name] = secret_arn

        self.logger.info(f"Retrieved {len(secrets)} secrets")
        return secrets

    def create_secret(
        self,
        name: str,
        secret_value: str,
        description: str = "",
        tags: Optional[dict[str, str]] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new secret in AWS Secrets Manager."""
        if not name:
            raise ValueError("name is required to create a secret")
        if is_nothing(secret_value):
            raise ValueError("secret_value is required to create a secret")

        self.logger.info(f"Creating AWS secret: {name}")
        role_arn = execution_role_arn or self.execution_role_arn
        secretsmanager = self.get_aws_client(
            client_name="secretsmanager",
            execution_role_arn=role_arn,
        )

        create_kwargs: dict[str, Any] = {"Name": name, "SecretString": secret_value}
        if description:
            create_kwargs["Description"] = description
        if tags:
            create_kwargs["Tags"] = [{"Key": key, "Value": value} for key, value in tags.items()]

        try:
            response = secretsmanager.create_secret(**create_kwargs)
            self.logger.info(f"Created AWS secret ARN: {response.get('ARN')}")
            return response
        except ClientError as exc:
            self.logger.error(f"Failed to create secret {name}", exc_info=True)
            raise RuntimeError(f"Failed to create secret '{name}'") from exc

    def update_secret(
        self,
        secret_id: str,
        secret_value: str,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update an existing secret value."""
        if not secret_id:
            raise ValueError("secret_id is required to update a secret")
        if is_nothing(secret_value):
            raise ValueError("secret_value is required to update a secret")

        self.logger.info(f"Updating AWS secret: {secret_id}")

        role_arn = execution_role_arn or self.execution_role_arn
        secretsmanager = self.get_aws_client(
            client_name="secretsmanager",
            execution_role_arn=role_arn,
        )

        try:
            response = secretsmanager.update_secret(SecretId=secret_id, SecretString=secret_value)
            self.logger.info(f"Updated AWS secret ARN: {response.get('ARN', secret_id)}")
            return response
        except ClientError as exc:
            self.logger.error(f"Failed to update secret {secret_id}", exc_info=True)
            raise RuntimeError(f"Failed to update secret '{secret_id}'") from exc

    def delete_secret(
        self,
        secret_id: str,
        force_delete: bool = False,
        recovery_window_days: int = 30,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete a secret from AWS Secrets Manager."""
        if not secret_id:
            raise ValueError("secret_id is required to delete a secret")

        if not force_delete and not 7 <= recovery_window_days <= 30:
            raise ValueError("recovery_window_days must be between 7 and 30 when not forcing deletion")

        self.logger.info(f"Deleting AWS secret: {secret_id}")

        role_arn = execution_role_arn or self.execution_role_arn
        secretsmanager = self.get_aws_client(
            client_name="secretsmanager",
            execution_role_arn=role_arn,
        )

        delete_kwargs: dict[str, Any] = {"SecretId": secret_id}
        if force_delete:
            delete_kwargs["ForceDeleteWithoutRecovery"] = True
        else:
            delete_kwargs["RecoveryWindowInDays"] = recovery_window_days

        try:
            response = secretsmanager.delete_secret(**delete_kwargs)
            self.logger.info(f"Delete secret request submitted for: {response.get('ARN', secret_id)}")
            return response
        except ClientError as exc:
            self.logger.error(f"Failed to delete secret {secret_id}", exc_info=True)
            raise RuntimeError(f"Failed to delete secret '{secret_id}'") from exc

    def delete_secrets_matching(
        self,
        name_prefix: str,
        force_delete: bool = False,
        dry_run: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> list[str]:
        """Delete all secrets that match the provided name prefix."""
        if not name_prefix:
            raise ValueError("name_prefix is required to delete matching secrets")

        self.logger.info(f"Deleting secrets matching prefix: {name_prefix} (dry_run={dry_run})")

        role_arn = execution_role_arn or self.execution_role_arn
        secrets = self.list_secrets(
            name_prefix=name_prefix,
            execution_role_arn=role_arn,
        )

        secret_arns: list[str] = []
        for secret_name, value in secrets.items():
            if isinstance(value, str):
                secret_arns.append(value)
            elif isinstance(value, dict) and "ARN" in value:
                secret_arns.append(value["ARN"])
            else:
                self.logger.debug(f"Skipping secret {secret_name} due to missing ARN data")

        if not secret_arns:
            self.logger.info(f"No secrets found for prefix: {name_prefix}")
            return []

        if dry_run:
            self.logger.info(f"Dry run enabled; would delete {len(secret_arns)} secrets for prefix {name_prefix}")
            return secret_arns

        deleted_arns: list[str] = []
        for secret_arn in secret_arns:
            response = self.delete_secret(
                secret_id=secret_arn,
                force_delete=force_delete,
                recovery_window_days=30,
                execution_role_arn=role_arn,
            )
            deleted_arns.append(response.get("ARN", secret_arn))

        self.logger.info(f"Deleted {len(deleted_arns)} secrets for prefix {name_prefix}")
        return deleted_arns

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
        import json as json_module

        self.logger.info(f"Copying {len(secrets)} secrets to s3://{bucket}/{key}")

        s3_client = self.get_aws_client(
            client_name="s3",
            execution_role_arn=execution_role_arn or self.execution_role_arn,
            role_session_name=role_session_name,
        )

        body = json_module.dumps(secrets)
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


# Import submodule operations to make them available
from vendor_connectors.aws.codedeploy import create_codedeploy_deployment, get_aws_codedeploy_deployments
from vendor_connectors.aws.organizations import AWSOrganizationsMixin
from vendor_connectors.aws.s3 import AWSS3Mixin
from vendor_connectors.aws.sso import AWSSSOmixin


class AWSConnectorFull(AWSConnector, AWSOrganizationsMixin, AWSSSOmixin, AWSS3Mixin):
    """Full AWS connector with all operations.

    This class combines the base AWSConnector with all operation mixins.
    Use this for full functionality, or use AWSConnector directly and
    import specific mixins as needed.
    """

    pass


__all__ = [
    "AWSConnector",
    "AWSConnectorFull",
    "AWSOrganizationsMixin",
    "AWSSSOmixin",
    "AWSS3Mixin",
    "get_aws_codedeploy_deployments",
    "create_codedeploy_deployment",
]
