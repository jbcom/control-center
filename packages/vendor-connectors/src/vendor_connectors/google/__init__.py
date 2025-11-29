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
from collections.abc import Sequence
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
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.orgunit.readonly",
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

    def get_connector_for_user(
        self,
        primary_email: str,
        scopes: Optional[list[str]] = None,
    ) -> GoogleConnector:
        """Get a connector instance impersonating a specific user.

        This is useful for terraform-style operations where you need to perform
        actions as a specific user rather than the service account.

        Args:
            primary_email: Email address of the user to impersonate.
            scopes: Optional custom scopes. Defaults to current connector's scopes.

        Returns:
            A new GoogleConnector instance configured to impersonate the user.
        """
        return GoogleConnector(
            service_account_info=self.service_account_info,
            scopes=scopes or self.scopes,
            subject=primary_email,
            logger=self.logging,
            inputs=self.inputs,
            from_environment=False,
            from_stdin=False,
        )

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
        """Get the Admin Directory API service."""
        return self.get_service("admin", "directory_v1", subject=subject)

    def get_cloud_resource_manager_service(self) -> Any:
        """Get the Cloud Resource Manager API service."""
        return self.get_service("cloudresourcemanager", "v3")

    def get_iam_service(self) -> Any:
        """Get the IAM API service."""
        return self.get_service("iam", "v1")

    def get_billing_service(self) -> Any:
        """Get the Cloud Billing API service."""
        return self.get_service("cloudbilling", "v1")

    def get_compute_service(self) -> Any:
        """Get the Compute Engine API service."""
        return self.get_service("compute", "v1")

    def get_container_service(self) -> Any:
        """Get the GKE API service."""
        return self.get_service("container", "v1")

    def get_storage_service(self) -> Any:
        """Get the Cloud Storage API service."""
        return self.get_service("storage", "v1")

    def get_sqladmin_service(self) -> Any:
        """Get the Cloud SQL Admin API service."""
        return self.get_service("sqladmin", "v1beta4")

    def get_pubsub_service(self) -> Any:
        """Get the Pub/Sub API service."""
        return self.get_service("pubsub", "v1")

    def get_serviceusage_service(self) -> Any:
        """Get the Service Usage API service."""
        return self.get_service("serviceusage", "v1")

    def get_cloudkms_service(self) -> Any:
        """Get the Cloud KMS API service."""
        return self.get_service("cloudkms", "v1")

    # =========================================================================
    # Directory Filtering Helpers (from PR #241)
    # =========================================================================

    def _resolve_bool_option(self, explicit: Optional[bool], input_key: str, default: bool) -> bool:
        """Resolve boolean options from parameters or directed inputs."""
        if explicit is not None:
            return explicit

        value = self.get_input(input_key, required=False, default=default, is_bool=True)
        if value is None:
            return default
        return bool(value)

    def _resolve_sequence_option(
        self,
        explicit: Sequence[str] | str | None,
        input_key: str,
    ) -> list[str] | None:
        """Resolve list-like options from parameters or directed inputs."""
        if explicit is not None:
            return self._normalize_str_sequence(explicit)

        raw_value = self.get_input(input_key, required=False)
        if isinstance(raw_value, str):
            candidate = raw_value.strip()
            if candidate:
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    pass
                else:
                    return self._normalize_str_sequence(parsed)

        return self._normalize_str_sequence(raw_value)

    @staticmethod
    def _normalize_str_sequence(value: Sequence[Any] | str | None) -> list[str] | None:
        """Normalize comma-delimited strings or sequences into clean string lists."""
        if value is None:
            return None

        if isinstance(value, str):
            normalized = [item.strip() for item in value.split(",") if item.strip()]
            return normalized or None

        normalized: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                normalized.append(text)

        return normalized or None

    @staticmethod
    def _normalize_org_unit_path(path: Optional[str]) -> Optional[str]:
        """Normalize OrgUnit identifiers to leading-slash paths."""
        if not path:
            return None

        clean = path.strip()
        if not clean:
            return None

        return clean if clean.startswith("/") else f"/{clean}"

    def _normalize_org_unit_list(self, values: list[str] | None) -> list[str] | None:
        """Normalize org unit inputs and discard empties."""
        if not values:
            return None

        normalized: list[str] = []
        for value in values:
            normalized_path = self._normalize_org_unit_path(value)
            if normalized_path:
                normalized.append(normalized_path)

        return normalized or None

    def _is_org_unit_allowed(
        self,
        entry: dict[str, Any],
        allow_list: list[str] | None,
        deny_list: list[str] | None,
    ) -> bool:
        """Check whether an entry's org unit is permitted by allow/deny lists."""
        if not allow_list and not deny_list:
            return True

        entry_path = self._normalize_org_unit_path(entry.get("orgUnitPath"))
        if entry_path is None:
            return not allow_list

        if allow_list and entry_path not in allow_list:
            return False

        if deny_list and entry_path in deny_list:
            return False

        return True

    @staticmethod
    def _is_bot_entry(entry: dict[str, Any]) -> bool:
        """Detect Google Workspace bot/service accounts."""
        return bool(
            entry.get("isBot")
            or entry.get("is_bot")
            or entry.get("type") in {"BOT", "bot"}
            or entry.get("kind") == "admin#directory#user#bot"
        )

    @staticmethod
    def _flatten_user_name(entry: dict[str, Any]) -> None:
        """Flatten the nested name structure for easier downstream consumption."""
        name_block = entry.get("name")
        if not isinstance(name_block, dict):
            return

        entry["full_name"] = name_block.get("fullName")
        entry["given_name"] = name_block.get("givenName")
        entry["family_name"] = name_block.get("familyName")

    @staticmethod
    def _key_results_by_email(
        entries: list[dict[str, Any]],
        *,
        primary_field: str,
        fallback_field: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Convert a list of directory entries into a dictionary keyed by email."""
        keyed: dict[str, dict[str, Any]] = {}
        for entry in entries:
            email = entry.get(primary_field) or (entry.get(fallback_field) if fallback_field else None)
            if not email:
                continue
            keyed[email] = entry
        return keyed

    def _filter_directory_entries(
        self,
        entries: list[dict[str, Any]],
        *,
        ou_allow_list: list[str] | None,
        ou_deny_list: list[str] | None,
        include_suspended: bool,
        exclude_bots: bool,
        flatten_names: bool,
    ) -> list[dict[str, Any]]:
        """Apply filtering and optional name flattening to directory results."""
        filtered: list[dict[str, Any]] = []
        for entry in entries:
            if not include_suspended and entry.get("suspended"):
                continue
            if exclude_bots and self._is_bot_entry(entry):
                continue
            if not self._is_org_unit_allowed(entry, ou_allow_list, ou_deny_list):
                continue

            processed = dict(entry)
            if flatten_names:
                self._flatten_user_name(processed)
            filtered.append(processed)

        return filtered

    # =========================================================================
    # Directory Listing with Filtering (from PR #241)
    # =========================================================================

    def list_users(
        self,
        domain: Optional[str] = None,
        max_results: int = 500,
        *,
        ou_allow_list: Sequence[str] | str | None = None,
        ou_deny_list: Sequence[str] | str | None = None,
        include_suspended: Optional[bool] = None,
        exclude_bots: Optional[bool] = None,
        flatten_names: Optional[bool] = None,
        key_by_email: Optional[bool] = None,
    ) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
        """List users from Google Workspace with optional filtering.

        Args:
            domain: Domain to list users from.
            max_results: Maximum results per page.
            ou_allow_list: Only include users from these OUs.
            ou_deny_list: Exclude users from these OUs.
            include_suspended: Include suspended users (default False).
            exclude_bots: Exclude service/bot accounts (default True).
            flatten_names: Flatten nested name structure (default False).
            key_by_email: Return dict keyed by email instead of list (default False).

        Returns:
            List of user dicts, or dict keyed by email if key_by_email=True.
        """
        service = self.get_admin_directory_service()
        users: list[dict[str, Any]] = []
        page_token = None

        while True:
            request = service.users().list(
                customer="my_customer",
                domain=domain,
                maxResults=max_results,
                pageToken=page_token,
            )
            response = request.execute()
            users.extend(response.get("users", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        ou_allow = self._normalize_org_unit_list(self._resolve_sequence_option(ou_allow_list, "ou_allow_list"))
        ou_deny = self._normalize_org_unit_list(self._resolve_sequence_option(ou_deny_list, "ou_deny_list"))
        include_inactive = self._resolve_bool_option(include_suspended, "include_suspended", False)
        omit_bots = self._resolve_bool_option(exclude_bots, "exclude_bots", True)
        should_flatten_names = self._resolve_bool_option(flatten_names, "flatten_names", False)
        return_keyed = self._resolve_bool_option(key_by_email, "key_by_email", False)

        filtered_users = self._filter_directory_entries(
            users,
            ou_allow_list=ou_allow,
            ou_deny_list=ou_deny,
            include_suspended=include_inactive,
            exclude_bots=omit_bots,
            flatten_names=should_flatten_names,
        )

        self.logger.info(
            "Retrieved %d users from Google Workspace (filtered to %d)",
            len(users),
            len(filtered_users),
        )

        if return_keyed:
            return self._key_results_by_email(filtered_users, primary_field="primaryEmail", fallback_field="email")

        return filtered_users

    def list_groups(
        self,
        domain: Optional[str] = None,
        max_results: int = 200,
        *,
        ou_allow_list: Sequence[str] | str | None = None,
        ou_deny_list: Sequence[str] | str | None = None,
        include_suspended: Optional[bool] = None,
        exclude_bots: Optional[bool] = None,
        flatten_names: Optional[bool] = None,
        key_by_email: Optional[bool] = None,
    ) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
        """List groups from Google Workspace with optional filtering.

        Args:
            domain: Domain to list groups from.
            max_results: Maximum results per page.
            ou_allow_list: Only include groups from these OUs.
            ou_deny_list: Exclude groups from these OUs.
            include_suspended: Include suspended groups (default False).
            exclude_bots: Exclude bot groups (default True).
            flatten_names: Flatten nested name structure (default False).
            key_by_email: Return dict keyed by email instead of list (default False).

        Returns:
            List of group dicts, or dict keyed by email if key_by_email=True.
        """
        service = self.get_admin_directory_service()
        groups: list[dict[str, Any]] = []
        page_token = None

        while True:
            request = service.groups().list(
                customer="my_customer",
                domain=domain,
                maxResults=max_results,
                pageToken=page_token,
            )
            response = request.execute()
            groups.extend(response.get("groups", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        ou_allow = self._normalize_org_unit_list(self._resolve_sequence_option(ou_allow_list, "ou_allow_list"))
        ou_deny = self._normalize_org_unit_list(self._resolve_sequence_option(ou_deny_list, "ou_deny_list"))
        include_inactive = self._resolve_bool_option(include_suspended, "include_suspended", False)
        omit_bots = self._resolve_bool_option(exclude_bots, "exclude_bots", True)
        should_flatten_names = self._resolve_bool_option(flatten_names, "flatten_names", False)
        return_keyed = self._resolve_bool_option(key_by_email, "key_by_email", False)

        filtered_groups = self._filter_directory_entries(
            groups,
            ou_allow_list=ou_allow,
            ou_deny_list=ou_deny,
            include_suspended=include_inactive,
            exclude_bots=omit_bots,
            flatten_names=should_flatten_names,
        )

        self.logger.info(
            "Retrieved %d groups from Google Workspace (filtered to %d)",
            len(groups),
            len(filtered_groups),
        )

        if return_keyed:
            return self._key_results_by_email(filtered_groups, primary_field="email", fallback_field="primaryEmail")

        return filtered_groups


# Import submodule operations
from vendor_connectors.google.billing import GoogleBillingMixin
from vendor_connectors.google.cloud import GoogleCloudMixin
from vendor_connectors.google.constants import (
    DEFAULT_DOMAIN,
    DEFAULT_USER_OUS,
    GCP_KMS,
    GCP_REQUIRED_APIS,
    GCP_REQUIRED_ORGANIZATION_ROLES,
    GCP_REQUIRED_ROLES,
    GCP_SECURITY_PROJECT,
)
from vendor_connectors.google.services import GoogleServicesMixin
from vendor_connectors.google.workspace import GoogleWorkspaceMixin


class GoogleConnectorFull(
    GoogleConnector, GoogleWorkspaceMixin, GoogleCloudMixin, GoogleBillingMixin, GoogleServicesMixin
):
    """Full Google connector with all operations.

    This class combines the base GoogleConnector with all operation mixins.
    Use this for full functionality, or use GoogleConnector directly and
    import specific mixins as needed.
    """

    pass


__all__ = [
    # Core connector classes
    "GoogleConnector",
    "GoogleConnectorFull",
    # Mixins
    "GoogleWorkspaceMixin",
    "GoogleCloudMixin",
    "GoogleBillingMixin",
    "GoogleServicesMixin",
    # Constants
    "DEFAULT_SCOPES",
    "DEFAULT_DOMAIN",
    "DEFAULT_USER_OUS",
    "GCP_SECURITY_PROJECT",
    "GCP_KMS",
    "GCP_REQUIRED_APIS",
    "GCP_REQUIRED_ORGANIZATION_ROLES",
    "GCP_REQUIRED_ROLES",
]
