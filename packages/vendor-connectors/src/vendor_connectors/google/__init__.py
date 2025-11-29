"""Google Cloud and Workspace Connector using jbcom ecosystem packages.

This package provides Google operations organized into submodules:
- workspace: Google Workspace (Admin Directory) user/group operations
- cloud: Google Cloud Platform resource management
- billing: Google Cloud Billing operations
- services: Google Cloud service discovery (GKE, Compute, SQL, etc.)

Usage:
    from vendor_connectors.google import GoogleConnector

    connector = GoogleConnector(service_account_info=...)
    users = connector.list_users()
"""

from __future__ import annotations

import json
from typing import Any, Optional

from directed_inputs_class import DirectedInputsClass
from google.oauth2 import service_account
from googleapiclient.discovery import build
from lifecyclelogging import Logging

# Default Google scopes
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-billing",
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]


class GoogleConnector(DirectedInputsClass):
    """Google Cloud and Workspace base connector.

    This is the base connector class providing:
    - Authentication via service account
    - Service client creation and caching
    - Subject impersonation for domain-wide delegation

    Higher-level operations are provided via mixin classes from submodules.
    """

    def __init__(
        self,
        service_account_info: Optional[dict[str, Any] | str] = None,
        scopes: Optional[list[str]] = None,
        subject: Optional[str] = None,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
        """Initialize the Google connector.

        Args:
            service_account_info: Service account JSON as dict or string.
                If not provided, reads from GOOGLE_SERVICE_ACCOUNT input.
            scopes: OAuth scopes to request. Defaults to common scopes.
            subject: Email to impersonate via domain-wide delegation.
            logger: Optional Logging instance.
            **kwargs: Additional arguments passed to DirectedInputsClass.
        """
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name="GoogleConnector")
        self.logger = self.logging.logger

        self.scopes = scopes or DEFAULT_SCOPES
        self.subject = subject

        # Get service account info from input if not provided
        if service_account_info is None:
            service_account_info = self.get_input("GOOGLE_SERVICE_ACCOUNT", required=True)

        # Parse if string
        if isinstance(service_account_info, str):
            service_account_info = json.loads(service_account_info)

        self.service_account_info = service_account_info
        self._credentials: Optional[service_account.Credentials] = None
        self._services: dict[str, Any] = {}

        self.logger.info("Initialized Google connector")

    # =========================================================================
    # Authentication
    # =========================================================================

    @property
    def credentials(self) -> service_account.Credentials:
        """Get or create Google credentials.

        Returns:
            Authenticated service account credentials.
        """
        if self._credentials is None:
            self._credentials = service_account.Credentials.from_service_account_info(
                self.service_account_info,
                scopes=self.scopes,
            )
            if self.subject:
                self._credentials = self._credentials.with_subject(self.subject)

        return self._credentials

    def get_credentials_for_subject(self, subject: str) -> service_account.Credentials:
        """Get credentials impersonating a specific user.

        Args:
            subject: Email address to impersonate.

        Returns:
            Credentials with the specified subject.
        """
        return service_account.Credentials.from_service_account_info(
            self.service_account_info,
            scopes=self.scopes,
        ).with_subject(subject)

    # =========================================================================
    # Service Client Creation
    # =========================================================================

    def get_service(self, service_name: str, version: str, subject: Optional[str] = None) -> Any:
        """Get a Google API service client.

        Args:
            service_name: Google API service name (e.g., 'admin', 'cloudresourcemanager').
            version: API version (e.g., 'v1', 'directory_v1').
            subject: Optional subject to impersonate for this service.

        Returns:
            Google API service client.
        """
        cache_key = f"{service_name}:{version}:{subject or ''}"
        if cache_key not in self._services:
            creds = self.get_credentials_for_subject(subject) if subject else self.credentials
            self._services[cache_key] = build(service_name, version, credentials=creds)
            self.logger.debug(f"Created Google service: {service_name} v{version}")
        return self._services[cache_key]

    # =========================================================================
    # Convenience Service Getters
    # =========================================================================

    def get_admin_directory_service(self, subject: Optional[str] = None) -> Any:
        """Get the Admin Directory API service.

        Args:
            subject: Optional email to impersonate.

        Returns:
            Admin Directory API service client.
        """
        return self.get_service("admin", "directory_v1", subject=subject)

    def get_cloud_resource_manager_service(self) -> Any:
        """Get the Cloud Resource Manager API service.

        Returns:
            Cloud Resource Manager API service client.
        """
        return self.get_service("cloudresourcemanager", "v3")

    def get_iam_service(self) -> Any:
        """Get the IAM API service.

        Returns:
            IAM API service client.
        """
        return self.get_service("iam", "v1")

    def get_billing_service(self) -> Any:
        """Get the Cloud Billing API service.

        Returns:
            Cloud Billing API service client.
        """
        return self.get_service("cloudbilling", "v1")

    def get_compute_service(self) -> Any:
        """Get the Compute Engine API service.

        Returns:
            Compute Engine API service client.
        """
        return self.get_service("compute", "v1")

    def get_container_service(self) -> Any:
        """Get the GKE API service.

        Returns:
            GKE API service client.
        """
        return self.get_service("container", "v1")

    def get_storage_service(self) -> Any:
        """Get the Cloud Storage API service.

        Returns:
            Cloud Storage API service client.
        """
        return self.get_service("storage", "v1")

    def get_sqladmin_service(self) -> Any:
        """Get the Cloud SQL Admin API service.

        Returns:
            Cloud SQL Admin API service client.
        """
        return self.get_service("sqladmin", "v1beta4")

    def get_pubsub_service(self) -> Any:
        """Get the Pub/Sub API service.

        Returns:
            Pub/Sub API service client.
        """
        return self.get_service("pubsub", "v1")

    def get_serviceusage_service(self) -> Any:
        """Get the Service Usage API service.

        Returns:
            Service Usage API service client.
        """
        return self.get_service("serviceusage", "v1")

    def get_cloudkms_service(self) -> Any:
        """Get the Cloud KMS API service.

        Returns:
            Cloud KMS API service client.
        """
        return self.get_service("cloudkms", "v1")


# Import submodule operations
from vendor_connectors.google.billing import GoogleBillingMixin
from vendor_connectors.google.cloud import GoogleCloudMixin
from vendor_connectors.google.services import GoogleServicesMixin
from vendor_connectors.google.workspace import GoogleWorkspaceMixin


class GoogleConnectorFull(GoogleConnector, GoogleWorkspaceMixin, GoogleCloudMixin, GoogleBillingMixin, GoogleServicesMixin):
    """Full Google connector with all operations.

    This class combines the base GoogleConnector with all operation mixins.
    Use this for full functionality, or use GoogleConnector directly and
    import specific mixins as needed.
    """
    pass


__all__ = [
    "GoogleConnector",
    "GoogleConnectorFull",
    "GoogleWorkspaceMixin",
    "GoogleCloudMixin",
    "GoogleBillingMixin",
    "GoogleServicesMixin",
    "DEFAULT_SCOPES",
]
