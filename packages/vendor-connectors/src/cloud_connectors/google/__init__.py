import json
from functools import cache, lru_cache
from typing import Any, Dict, List, Optional, Union

import googleapiclient.discovery
from google.api_core import retry
from google.auth.transport.requests import Request
from google.cloud import billing_v1, resourcemanager_v3
from google.oauth2 import service_account

from cloud_connectors.base.utils import Utils, get_default_dict

CLOUD_CLIENTS = {
    "billing": {
        "v1": billing_v1.CloudBillingClient,
    },
    "resourcemanager": {
        "v3": resourcemanager_v3.ProjectsClient,
    },
}


class GoogleConnector(Utils):
    """
    Google Client with lazy credential loading for both Workspace and Cloud Platform APIs.
    """

    def __init__(
        self,
        scopes: list[str],
        service_account_file: Union[str, dict[str, Any]],
        subject: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.scopes = scopes
        self._parse_service_account(service_account_file)

        # Set subject but don't authenticate yet
        self.subject = subject or self.service_account_file.get("client_email")
        if not self.subject:
            raise ValueError("Subject is required or must be in service account file")

        # Initialize credential placeholders
        self._credentials = {}  # Cache for workspace credentials by subject
        self._cloud_credentials = None

        # Service cache
        self.services = get_default_dict(levels=3)

        self.logger.debug("Client initialized with lazy credential loading")

    def _parse_service_account(self, service_account_file: Union[str, dict[str, Any]]) -> None:
        """Parse and validate service account file."""
        if isinstance(service_account_file, str):
            try:
                self.service_account_file = json.loads(service_account_file)
                self.logger.debug("Successfully parsed service account JSON string")
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse service account JSON: {e}")
                raise
        elif isinstance(service_account_file, dict):
            self.service_account_file = service_account_file
        else:
            self.logger.error("Invalid service account file format")
            raise ValueError("Service account file must be a JSON string or dictionary")

        # Verify required fields
        required_fields = {"client_email", "private_key", "project_id"}
        missing_fields = required_fields - self.service_account_file.keys()
        if missing_fields:
            raise ValueError(f"Service account file missing required fields: {missing_fields}")

    def _get_workspace_credentials(self, subject: str) -> service_account.Credentials:
        """
        Get or create Workspace credentials for a specific subject.
        Lazy loads credentials only when needed.
        """
        credentials = self._credentials.get(subject)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                base_credentials = service_account.Credentials.from_service_account_info(
                    self.service_account_file,
                    scopes=self.scopes,
                    subject=self.subject,
                )

                if subject != self.subject:
                    credentials = base_credentials.create_delegated(subject)
                else:
                    credentials = base_credentials

                self._credentials[subject] = credentials
                self.logger.debug(f"Created new credentials for subject: {subject}")

        return credentials

    def _get_cloud_credentials(self) -> service_account.Credentials:
        """
        Get or create Cloud Platform credentials.
        Lazy loads credentials only when needed.
        """
        if not self._cloud_credentials or not self._cloud_credentials.valid:
            if self._cloud_credentials and self._cloud_credentials.expired:
                self._cloud_credentials.refresh(Request())
            else:
                self._cloud_credentials = service_account.Credentials.from_service_account_info(
                    self.service_account_file,
                    scopes=self.scopes,
                )
                self.logger.debug("Created new cloud credentials")

        return self._cloud_credentials

    @cache
    def _is_cloud_service(self, service_name: str, version_name: str) -> bool:
        """Determine if a service is a Cloud Platform service."""
        return service_name in CLOUD_CLIENTS and version_name in CLOUD_CLIENTS[service_name]

    def get_service(self, service_name: str, version_name: str, user_email: Optional[str] = None) -> Any:
        """
        Get a service client, creating it and its credentials only when first needed.

        Args:
            service_name: Service name (e.g., 'admin', 'drive', 'billing')
            version_name: API version (e.g., 'v1', 'v3')
            user_email: Optional email to impersonate (for Workspace APIs)

        Returns:
            Either a Workspace service client or Cloud Platform client
        """
        subject = user_email or self.subject

        # Check cache first
        if (
            subject in self.services
            and service_name in self.services[subject]
            and version_name in self.services[subject][service_name]
        ):
            return self.services[subject][service_name][version_name]

        # Determine service type and get appropriate credentials
        is_cloud = self._is_cloud_service(service_name, version_name)

        try:
            if is_cloud:
                credentials = self._get_cloud_credentials()
                service = CLOUD_CLIENTS[service_name][version_name](credentials=credentials)
                self.logger.debug(f"Created new cloud service: {service_name} {version_name}")
            else:
                credentials = self._get_workspace_credentials(subject)
                service = googleapiclient.discovery.build(
                    serviceName=service_name,
                    version=version_name,
                    credentials=credentials,
                )
                self.logger.debug(f"Created new workspace service: {service_name} {version_name}")

            # Cache the service
            if subject not in self.services:
                self.services[subject] = {}
            if service_name not in self.services[subject]:
                self.services[subject][service_name] = {}
            self.services[subject][service_name][version_name] = service

            return service

        except Exception as e:
            self.logger.error(f"Failed to create service {service_name} {version_name}: {str(e)}")
            raise
