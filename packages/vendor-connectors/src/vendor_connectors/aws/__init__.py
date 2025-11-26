"""AWS Connector using jbcom ecosystem packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import boto3
from boto3.resources.base import ServiceResource
from botocore.config import Config
from botocore.exceptions import ClientError
from directed_inputs_class import DirectedInputsClass
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
