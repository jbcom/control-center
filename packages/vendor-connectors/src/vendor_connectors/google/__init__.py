"""Google Connector using jbcom ecosystem packages."""

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
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]


class GoogleConnector(DirectedInputsClass):
    """Google Cloud and Workspace connector."""

    def __init__(
        self,
        service_account_info: Optional[dict[str, Any] | str] = None,
        scopes: Optional[list[str]] = None,
        subject: Optional[str] = None,
        logger: Optional[Logging] = None,
        **kwargs,
    ):
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

    @property
    def credentials(self) -> service_account.Credentials:
        """Get or create Google credentials."""
        if self._credentials is None:
            self._credentials = service_account.Credentials.from_service_account_info(
                self.service_account_info,
                scopes=self.scopes,
            )
            if self.subject:
                self._credentials = self._credentials.with_subject(self.subject)

        return self._credentials

    def get_service(self, service_name: str, version: str) -> Any:
        """Get a Google API service client."""
        cache_key = f"{service_name}:{version}"
        if cache_key not in self._services:
            self._services[cache_key] = build(service_name, version, credentials=self.credentials)
            self.logger.info(f"Created Google service: {service_name} v{version}")
        return self._services[cache_key]

    def get_admin_directory_service(self) -> Any:
        """Get the Admin Directory API service."""
        return self.get_service("admin", "directory_v1")

    def get_cloud_resource_manager_service(self) -> Any:
        """Get the Cloud Resource Manager API service."""
        return self.get_service("cloudresourcemanager", "v3")

    def get_iam_service(self) -> Any:
        """Get the IAM API service."""
        return self.get_service("iam", "v1")

    def list_users(self, domain: Optional[str] = None, max_results: int = 500) -> list[dict[str, Any]]:
        """List users from Google Workspace."""
        service = self.get_admin_directory_service()
        users: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"customer": "my_customer", "maxResults": max_results}
            if domain:
                params["domain"] = domain
            if page_token:
                params["pageToken"] = page_token

            response = service.users().list(**params).execute()
            users.extend(response.get("users", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(users)} users from Google Workspace")
        return users

    def list_groups(self, domain: Optional[str] = None, max_results: int = 200) -> list[dict[str, Any]]:
        """List groups from Google Workspace."""
        service = self.get_admin_directory_service()
        groups: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"customer": "my_customer", "maxResults": max_results}
            if domain:
                params["domain"] = domain
            if page_token:
                params["pageToken"] = page_token

            response = service.groups().list(**params).execute()
            groups.extend(response.get("groups", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(groups)} groups from Google Workspace")
        return groups
