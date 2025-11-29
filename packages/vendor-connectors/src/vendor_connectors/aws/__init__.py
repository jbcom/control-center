"""AWS Connector using jbcom ecosystem packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

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
        """
        self.logger.info("Listing AWS Secrets Manager secrets")

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
