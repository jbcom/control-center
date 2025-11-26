from typing import Optional, Dict

import boto3
from boto3.resources.base import ServiceResource
from botocore.config import Config
from botocore.exceptions import ClientError

from cloud_connectors.base.utils import Utils


class AWSConnector(Utils):
    def __init__(self, execution_role_arn: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.execution_role_arn = execution_role_arn
        self.aws_sessions = {}
        self.aws_clients: Dict[str, Dict[str, boto3.client]] = {}
        self.default_aws_session = boto3.Session()

    def assume_role(self, execution_role_arn: str, role_session_name: str) -> boto3.Session:
        """
        Assume an AWS IAM role and return a boto3 Session using temporary credentials.
        """
        self.logged_statement(
            f"Attempting to assume role: {execution_role_arn}",
            identifiers=[role_session_name],
            log_level="info",
        )

        sts_client = self.default_aws_session.client("sts")

        try:
            response = sts_client.assume_role(
                RoleArn=execution_role_arn,
                RoleSessionName=role_session_name
            )
            credentials = response["Credentials"]

            self.logged_statement(
                f"Successfully assumed role: {execution_role_arn}",
                labeled_json_data={
                    "Session": {
                        "AccessKeyId": credentials["AccessKeyId"],
                        "SessionToken": credentials["SessionToken"][:10] + "...",
                        "Expiration": credentials["Expiration"].isoformat(),
                    }
                },
                log_level="info",
            )

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
        """
        Get a boto3 Session for the specified role, or the default session if no role is provided.
        """
        if not execution_role_arn:
            self.logger.info("Using default AWS session")
            return self.default_aws_session

        if execution_role_arn not in self.aws_sessions:
            self.aws_sessions[execution_role_arn] = {}

        if not role_session_name:
            role_session_name = self.get_unique_signature(delim=".")

        if role_session_name not in self.aws_sessions[execution_role_arn]:
            self.logged_statement(
                f"Creating new session for role: {execution_role_arn}",
                identifiers=[role_session_name],
                log_level="debug",
            )
            self.aws_sessions[execution_role_arn][role_session_name] = self.assume_role(
                execution_role_arn, role_session_name
            )
        else:
            self.logged_statement(
                f"Using cached session for role: {execution_role_arn}",
                identifiers=[role_session_name],
                log_level="debug",
            )

        return self.aws_sessions[execution_role_arn][role_session_name]

    @staticmethod
    def create_standard_retry_config(max_attempts: int = 5) -> Config:
        """
        Create a standard retry configuration with the specified maximum attempts.
        
        Args:
            max_attempts (int): Maximum number of attempts (including the initial request)
                                Default is 5 (initial request + 4 retries)
        
        Returns:
            Config: Botocore Config object with standard retry configuration
        """
        return Config(
            retries={
                'max_attempts': max_attempts,
                'mode': 'standard'
            }
        )

    def get_aws_client(
            self,
            client_name: str,
            execution_role_arn: Optional[str] = None,
            role_session_name: Optional[str] = None,
            config: Optional[Config] = None,
            **client_args,
    ) -> boto3.client:
        """
        Get a boto3 client for the specified service and role.

        Args:
            client_name (str): Name of the AWS service (e.g., 's3', 'sso-admin').
            execution_role_arn (Optional[str]): ARN of the role to assume.
            role_session_name (Optional[str]): Session name for the assumed role.
            config (Optional[Config]): Botocore Config object for client configuration including retries.
                                      If None, a standard retry config will be used.
            **client_args: Additional arguments passed to the boto3 client.

        Returns:
            boto3.client: Boto3 client for the specified service.
        """
        session = self.get_aws_session(execution_role_arn, role_session_name)

        # Use standard retry config if none is provided
        if config is None:
            config = self.create_standard_retry_config()
            self.logged_statement(
                f"No config provided for {client_name} client, using standard retry configuration",
                labeled_json_data={"retry_config": config.retries},
                log_level="debug",
            )
        else:
            # Log client creation with custom config details
            retry_config = config.retries if hasattr(config, 'retries') else None
            self.logged_statement(
                f"Creating {client_name} client with custom configuration",
                labeled_json_data={
                    "client_name": client_name,
                    "retry_config": retry_config,
                },
                log_level="debug",
            )

        # Create client with config
        return session.client(client_name, config=config, **client_args)

    def get_aws_resource(
            self,
            service_name: str,
            execution_role_arn: Optional[str] = None,
            role_session_name: Optional[str] = None,
            config: Optional[Config] = None,
            **resource_args,
    ) -> ServiceResource:
        """
        Get a boto3 resource for the specified service and role.

        Args:
            service_name (str): Name of the AWS service (e.g., 's3', 'dynamodb').
            execution_role_arn (Optional[str]): ARN of the role to assume.
            role_session_name (Optional[str]): Session name for the assumed role.
            config (Optional[Config]): Botocore Config object for resource configuration including retries.
                                      If None, a standard retry config will be used.
            **resource_args: Additional arguments passed to the boto3 resource.

        Returns:
            ServiceResource: Boto3 resource for the specified service.
        """
        session = self.get_aws_session(execution_role_arn, role_session_name)

        # Use standard retry config if none is provided
        if config is None:
            config = self.create_standard_retry_config()
            self.logged_statement(
                f"No config provided for {service_name} resource, using standard retry configuration",
                labeled_json_data={"retry_config": config.retries},
                log_level="debug",
            )

        # Include config information in logging
        log_data = {
            "execution_role_arn": execution_role_arn,
            "role_session_name": role_session_name,
            "resource_args": resource_args,
            "retry_config": config.retries if hasattr(config, 'retries') else None
        }

        self.logged_statement(
            f"Creating resource for service: {service_name}",
            labeled_json_data=log_data,
            log_level="debug",
        )

        try:
            # Create resource with config
            resource = session.resource(service_name, config=config, **resource_args)

            self.logged_statement(
                f"Successfully created resource for service: {service_name}",
                log_level="info",
            )
            return resource
        except ClientError as e:
            self.logger.error(f"Failed to create resource for service: {service_name}", exc_info=True)
            raise RuntimeError(f"Failed to create resource for service {service_name}") from e
