"""Google Connector using jbcom ecosystem packages."""

from __future__ import annotations

import json
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Optional

from directed_inputs_class import DirectedInputsClass
from extended_data_types import is_nothing, unhump_map
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from lifecyclelogging import Logging

from vendor_connectors.cloud_params import get_google_call_params

DEFAULT_DOMAIN = "flipsidecrypto.com"

# Default scopes now mirror terraform-modules to maintain feature parity.
DEFAULT_SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/apps.alerts",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/cloud-identity",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.activity",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.userschema",
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/admin.directory.orgunit",
    "https://www.googleapis.com/auth/apps.groups.settings",
    "https://www.googleapis.com/auth/apps.licensing",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-billing",
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/iam",
    "https://www.googleapis.com/auth/compute",
    "https://www.googleapis.com/auth/cloudkms",
    "https://www.googleapis.com/auth/logging.admin",
    "https://www.googleapis.com/auth/monitoring",
    "https://www.googleapis.com/auth/sqlservice.admin",
    "https://www.googleapis.com/auth/devstorage.full_control",
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/service.management",
]


def _to_tuple(values: Optional[Iterable[str]]) -> tuple[str, ...]:
    """Normalize optional iterables into tuples."""

    if values is None:
        return tuple()
    if isinstance(values, str):
        return (values,)
    return tuple(v for v in values if v)


def _flatten_name_fields(user_data: dict[str, Any]) -> None:
    """Flatten the nested name payload into the user dictionary."""

    name_payload = user_data.pop("name", None)
    if isinstance(name_payload, dict):
        for key, value in name_payload.items():
            if key in user_data:
                user_data[f"name_{key}"] = value
            else:
                user_data[key] = value


def _unhump_members_map(members: dict[str, Any]) -> dict[str, Any]:
    """Snake_case member payloads while keeping the email keys intact."""

    return {email: unhump_map(member) for email, member in members.items()}


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

        if service_account_info is None:
            service_account_info = self.get_input("GOOGLE_SERVICE_ACCOUNT", required=True)

        if isinstance(service_account_info, str):
            service_account_info = json.loads(service_account_info)

        self.service_account_info = deepcopy(service_account_info)
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

    def get_groups_settings_service(self) -> Any:
        """Get the Groups Settings API service."""

        return self.get_service("groupssettings", "v1")

    def get_cloud_resource_manager_service(self) -> Any:
        """Get the Cloud Resource Manager API service."""

        return self.get_service("cloudresourcemanager", "v3")

    def get_iam_service(self) -> Any:
        """Get the IAM API service."""

        return self.get_service("iam", "v1")

    # ------------------------------------------------------------------
    # Workspace helpers
    # ------------------------------------------------------------------
    def get_google_client_for_user(
        self,
        primary_email: str,
        scopes: Optional[list[str]] = None,
    ) -> "GoogleConnector":
        """Return a connector that impersonates a specific user."""

        return GoogleConnector(
            service_account_info=self.service_account_info,
            scopes=scopes or self.scopes,
            subject=primary_email,
            logger=self.logging,
            inputs=self.inputs,
            from_environment=False,
            from_stdin=False,
        )

    def get_google_users(
        self,
        *,
        unhump_users: Optional[bool] = None,
        flatten_name: Optional[bool] = None,
        allowed_ous: Optional[Iterable[str]] = None,
        denied_ous: Optional[Iterable[str]] = None,
        active_only: Optional[bool] = None,
        include_bots: Optional[bool] = None,
        domain: Optional[str] = None,
        customer: Optional[str] = None,
        max_results: int = 500,
    ) -> dict[str, dict[str, Any]]:
        """Fetch Google Workspace users with terraform-style filters."""

        if unhump_users is None:
            unhump_users = self.get_input("unhump_users", required=False, default=True, is_bool=True)
        if flatten_name is None:
            flatten_name = self.get_input("flatten_name", required=False, default=False, is_bool=True)
        if allowed_ous is None:
            allowed_ous = self.decode_input(
                "allowed_ous",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )
        if denied_ous is None:
            denied_ous = self.decode_input(
                "denied_ous",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )
        if active_only is None:
            active_only = self.get_input("active_only", required=False, default=False, is_bool=True)
        if include_bots is None:
            include_bots = self.get_input("include_bots", required=False, default=True, is_bool=True)
        if domain is None:
            domain = self.get_input("google_domain", required=False) or DEFAULT_DOMAIN
        if customer is None:
            customer = self.get_input("google_customer", required=False) or "my_customer"

        service = self.get_admin_directory_service()
        users: dict[str, dict[str, Any]] = {}
        allowed = set(_to_tuple(allowed_ous))
        denied = set(_to_tuple(denied_ous))

        page_token: str | None = None
        while True:
            params = get_google_call_params(
                max_results=max_results,
                domain=domain,
                customer=customer if is_nothing(domain) else None,
                pageToken=page_token,
            )
            response = service.users().list(**params).execute()

            for user in response.get("users", []):
                primary_email = user.get("primaryEmail")
                if not primary_email:
                    continue

                suspended = user.get("suspended")
                archived = user.get("archived")
                org_unit_path = user.get("orgUnitPath")

                if active_only and (suspended or archived):
                    continue

                if allowed and org_unit_path not in allowed:
                    continue

                if denied and org_unit_path in denied:
                    continue

                if (not include_bots) and isinstance(org_unit_path, str) and org_unit_path.startswith("/Automation"):
                    continue

                user_payload = deepcopy(user)

                if flatten_name:
                    _flatten_name_fields(user_payload)

                users[primary_email] = user_payload

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        if unhump_users:
            users = {email: unhump_map(payload) for email, payload in users.items()}

        self.logger.info(f"Retrieved {len(users)} filtered Google users")
        return users

    def list_users(self, domain: Optional[str] = None, max_results: int = 500) -> list[dict[str, Any]]:
        """Compat wrapper returning a list instead of a keyed dictionary."""

        users = self.get_google_users(
            domain=domain,
            unhump_users=False,
            flatten_name=False,
            max_results=max_results,
        )
        return list(users.values())

    def get_google_groups(
        self,
        *,
        group_keys: Optional[Iterable[str]] = None,
        group_names: Optional[Iterable[str]] = None,
        user_key: Optional[str] = None,
        domain: Optional[str] = None,
        unhump_groups: Optional[bool] = None,
        members_only: Optional[bool] = None,
        only_status_for_members: Optional[str] = None,
        only_type_for_members: Optional[str] = None,
        flatten_members: Optional[bool] = None,
        sort_by_name: Optional[bool] = None,
        max_results: int = 200,
    ) -> dict[str, Any]:
        """Retrieve Google groups, merging settings and membership details."""

        if unhump_groups is None:
            unhump_groups = self.get_input("unhump_groups", required=False, default=True, is_bool=True)
        if members_only is None:
            members_only = self.get_input("members_only", required=False, default=False, is_bool=True)
        if flatten_members is None:
            flatten_members = self.get_input("flatten_members", required=False, default=False, is_bool=True)
        if group_keys is None:
            group_keys = self.decode_input(
                "group_keys",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )
        if group_names is None:
            group_names = self.decode_input(
                "group_names",
                required=False,
                decode_from_base64=False,
            )
        if user_key is None:
            user_key = self.get_input("user_key", required=False)
        if sort_by_name is None:
            sort_by_name = self.get_input("sort_by_name", required=False, default=False, is_bool=True)
        if domain is None:
            domain = self.get_input("google_domain", required=False) or DEFAULT_DOMAIN

        directory = self.get_admin_directory_service()
        settings = self.get_groups_settings_service()
        results: dict[str, Any] = {}

        normalized_group_names = {name.lower() for name in _to_tuple(group_names)} if group_names else set()
        pending_keys = list(_to_tuple(group_keys))

        def should_include(group_payload: dict[str, Any]) -> bool:
            if not normalized_group_names:
                return True
            name = (group_payload.get("name") or "").lower()
            email = (group_payload.get("email") or "").lower()
            return name in normalized_group_names or email in normalized_group_names

        def fetch_members(group_key: str) -> dict[str, Any] | list[str]:
            member_payload: dict[str, Any] = {}
            members_resource = directory.members()
            members_page: Optional[str] = None
            while True:
                params = get_google_call_params(groupKey=group_key, pageToken=members_page)
                response = members_resource.list(**params).execute()
                for member in response.get("members", []):
                    if only_status_for_members and member.get("status") != only_status_for_members:
                        continue
                    if only_type_for_members and member.get("type") != only_type_for_members:
                        continue
                    member_email = member.get("email")
                    if member_email:
                        member_payload[member_email] = member
                members_page = response.get("nextPageToken")
                if not members_page:
                    break

            if flatten_members:
                return list(member_payload.keys())
            return member_payload

        def add_group(group_payload: dict[str, Any]) -> None:
            group_key = group_payload.get("email")
            if not group_key or not should_include(group_payload):
                return

            try:
                settings_payload = settings.groups().get(groupUniqueId=group_key).execute()
            except HttpError as err:  # pragma: no cover - network failure logging only
                raise RuntimeError(f"Unable to retrieve group settings for {group_key}") from err

            merged_group = self.merger.merge(group_payload, settings_payload)
            members = fetch_members(group_key)

            if members_only:
                results[group_key] = members
            else:
                merged_group["members"] = members
                results[group_key] = merged_group

        if pending_keys:
            for key in pending_keys:
                response = directory.groups().get(groupKey=key).execute()
                add_group(response)
        else:
            next_page: Optional[str] = None
            while True:
                params = get_google_call_params(
                    max_results=max_results,
                    domain=domain,
                    userKey=user_key,
                    pageToken=next_page,
                )
                response = directory.groups().list(**params).execute()
                for group in response.get("groups", []):
                    add_group(group)
                next_page = response.get("nextPageToken")
                if not next_page:
                    break

        if sort_by_name and not members_only:
            results = dict(
                sorted(
                    results.items(),
                    key=lambda item: (item[1].get("name") or item[0]).lower(),
                )
            )

        if unhump_groups:
            if members_only and not flatten_members:
                results = {
                    key: _unhump_members_map(member_payload)
                    if isinstance(member_payload, dict)
                    else member_payload
                    for key, member_payload in results.items()
                }
            elif not members_only:
                normalized: dict[str, Any] = {}
                for group_key, payload in results.items():
                    members_payload = payload.get("members")
                    base_payload = {k: v for k, v in payload.items() if k != "members"}
                    normalized_group = unhump_map(base_payload)
                    if isinstance(members_payload, dict) and not flatten_members:
                        normalized_group["members"] = _unhump_members_map(members_payload)
                    else:
                        normalized_group["members"] = members_payload
                    normalized[group_key] = normalized_group
                results = normalized

        self.logger.info(f"Retrieved {len(results)} Google groups")
        return results

    def list_groups(self, domain: Optional[str] = None, max_results: int = 200) -> list[dict[str, Any]]:
        """Compat wrapper returning a list of group payloads."""

        groups = self.get_google_groups(
            domain=domain,
            max_results=max_results,
            unhump_groups=False,
            members_only=False,
            flatten_members=False,
            sort_by_name=False,
        )
        return list(groups.values())

    def create_google_user(
        self,
        *,
        given_name: Optional[str] = None,
        family_name: Optional[str] = None,
        user_password: Optional[str] = None,
        primary_email: Optional[str] = None,
        additional_fields: Optional[dict[str, Any]] = None,
        update_if_exists: bool = False,
    ) -> dict[str, Any]:
        """Create (or optionally update) a Google Workspace user."""

        if given_name is None:
            given_name = self.get_input("given_name", required=True)
        if family_name is None:
            family_name = self.get_input("family_name", required=True)
        if user_password is None:
            user_password = self.get_input("user_password", required=True)
        if primary_email is None:
            primary_email = self.get_input("primary_email", required=True)

        directory = self.get_admin_directory_service()
        users_resource = directory.users()

        body: dict[str, Any] = {
            "name": {"givenName": given_name, "familyName": family_name},
            "password": user_password,
            "primaryEmail": primary_email,
        }
        if additional_fields:
            body = self.merger.merge(body, deepcopy(additional_fields))

        try:
            existing = users_resource.get(userKey=primary_email).execute()
            if update_if_exists:
                updated = users_resource.update(userKey=primary_email, body=body).execute()
                self.logger.info(f"Updated Google user {primary_email}")
                return updated
            self.logger.info(f"Google user already exists: {primary_email}")
            return existing
        except HttpError as err:
            if getattr(err, "resp", None) is None or err.resp.status != 404:
                raise

        created = users_resource.insert(body=body).execute()
        self.logger.info(f"Created Google user: {primary_email}")
        return created

    def create_google_group(
        self,
        *,
        group_email: Optional[str] = None,
        group_name: Optional[str] = None,
        additional_fields: Optional[dict[str, Any]] = None,
        update_if_exists: bool = False,
    ) -> dict[str, Any]:
        """Create (or optionally update) a Google Workspace group."""

        if group_email is None:
            group_email = self.get_input("group_email", required=True)
        if group_name is None:
            group_name = self.get_input("group_name", required=True)

        directory = self.get_admin_directory_service()
        groups_resource = directory.groups()

        body: dict[str, Any] = {"email": group_email, "name": group_name}
        if additional_fields:
            body = self.merger.merge(body, deepcopy(additional_fields))

        try:
            existing = groups_resource.get(groupKey=group_email).execute()
            if update_if_exists:
                updated = groups_resource.update(groupKey=group_email, body=body).execute()
                self.logger.info(f"Updated Google group {group_email}")
                return updated
            self.logger.info(f"Google group already exists: {group_email}")
            return existing
        except HttpError as err:
            if getattr(err, "resp", None) is None or err.resp.status != 404:
                raise

        created = groups_resource.insert(body=body).execute()
        self.logger.info(f"Created Google group: {group_email}")
        return created
