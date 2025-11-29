"""Google Connector using jbcom ecosystem packages."""

from __future__ import annotations

import json
import ssl
import time
from collections import defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime, timedelta
from http.client import IncompleteRead
from pathlib import Path
from typing import Any, Optional, Sequence

from directed_inputs_class import DirectedInputsClass
from extended_data_types import is_nothing, unhump_map
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from lifecyclelogging import Logging

from vendor_connectors.cloud_params import get_google_call_params
from vendor_connectors.google.constants import (
    DEFAULT_DOMAIN,
    DEFAULT_SCOPES,
    GCP_KMS,
    GCP_REQUIRED_APIS,
    GCP_REQUIRED_ORGANIZATION_ROLES,
    GCP_REQUIRED_ROLES,
    GCP_SECURITY_PROJECT,
)


_UNSET = object()


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

    def _with_overrides(
        self,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
        scopes: Optional[list[str]] = None,
        subject: object = _UNSET,
    ) -> "GoogleConnector":
        """Clone the connector with optional overrides."""

        if service_account_info is None and scopes is None and subject is _UNSET:
            return self

        effective_info = service_account_info if service_account_info is not None else self.service_account_info
        effective_subject = self.subject if subject is _UNSET else subject
        effective_scopes = scopes or self.scopes

        return type(self)(
            service_account_info=deepcopy(effective_info),
            scopes=effective_scopes,
            subject=effective_subject,
            logger=self.logging,
            inputs=self.inputs,
            from_environment=False,
            from_stdin=False,
        )

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

    # ------------------------------------------------------------------
    # Cloud organization & project helpers
    # ------------------------------------------------------------------
    def get_google_organization_id(
        self,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> str:
        """Retrieve the first organization ID visible to the connector."""

        client = self._with_overrides(service_account_info=service_account_info)
        crm = client.get_service("cloudresourcemanager", "v1")

        try:
            response = crm.organizations().search(body={}).execute()
        except HttpError as err:
            raise RuntimeError("Failed to retrieve Google organizations") from err

        organizations = response.get("organizations") or []
        if not organizations:
            raise ValueError("No Google organizations available to the service account")
        return organizations[0]["name"].split("/")[-1]

    def get_google_billing_accounts(
        self,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return all billing accounts accessible to the connector."""

        client = self._with_overrides(service_account_info=service_account_info)
        billing = client.get_service("cloudbilling", "v1")

        billing_accounts: dict[str, Any] = {}
        request = billing.billingAccounts().list()
        while request is not None:
            response = request.execute()
            for account in response.get("billingAccounts", []):
                account_id = (account.get("name") or "").split("/")[-1]
                if account_id:
                    billing_accounts[account_id] = account
            request = billing.billingAccounts().list_next(
                previous_request=request,
                previous_response=response,
            )
        return billing_accounts

    def get_google_billing_account(
        self,
        billing_account_name: Optional[str] = None,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> str:
        """Resolve a billing account ID from its display name."""

        billing_account_name = billing_account_name or "Primary"
        billing_accounts = self.get_google_billing_accounts(
            service_account_info=service_account_info,
        )
        for account_id, account in billing_accounts.items():
            if account.get("displayName") == billing_account_name:
                return account_id
        raise ValueError(f"Billing account '{billing_account_name}' not found")

    def get_google_billing_account_for_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
        max_retries: int = 3,
        retry_delay: int = 2,
    ) -> Optional[str]:
        """Return the billing account ID currently linked to a project."""

        client = self._with_overrides(service_account_info=service_account_info)
        billing = client.get_service("cloudbilling", "v1")

        attempt = 0
        last_error: Optional[Exception] = None
        while attempt < max_retries:
            try:
                info = (
                    billing.projects()
                    .getBillingInfo(name=f"projects/{project_id}")
                    .execute()
                )
                billing_name = info.get("billingAccountName")
                return billing_name.split("/")[-1] if billing_name else None
            except HttpError as err:
                last_error = err
                if err.resp.status == 429:
                    time.sleep(retry_delay)
                elif err.resp.status == 404:
                    return None
                else:
                    raise
            except (ssl.SSLError, ConnectionError, IncompleteRead) as err:  # type: ignore[misc]
                last_error = err
                time.sleep(retry_delay)
            attempt += 1

        if last_error:
            raise RuntimeError(
                f"Unable to retrieve billing account for project '{project_id}'"
            ) from last_error
        return None

    def get_google_projects(
        self,
        *,
        organization_id: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
        key_results_by: str = "projectId",
    ) -> dict[str, Any]:
        """Return all projects for an organization enriched with billing info."""

        client = self._with_overrides(service_account_info=service_account_info)
        crm = client.get_service("cloudresourcemanager", "v1")
        cloud_billing = client.get_service("cloudbilling", "v1")

        if not organization_id:
            organization_id = self.get_google_organization_id(
                service_account_info=service_account_info,
            )

        billing_accounts = self.get_google_billing_accounts(
            service_account_info=service_account_info,
        )

        billing_account_projects: dict[str, str] = {}
        for account_id in billing_accounts:
            request = (
                cloud_billing.billingAccounts()
                .projects()
                .list(name=f"billingAccounts/{account_id}")
            )
            while request is not None:
                response = request.execute()
                for project_info in response.get("projectBillingInfo", []):
                    project_key = project_info.get("projectId")
                    if project_key:
                        billing_account_projects[project_key] = account_id
                request = cloud_billing.billingAccounts().projects().list_next(
                    previous_request=request,
                    previous_response=response,
                )

        projects: dict[str, Any] = {}
        request = crm.projects().list()
        while request is not None:
            response = request.execute()
            for project in response.get("projects", []):
                parent = project.get("parent", {})
                if parent.get("type") != "organization" or parent.get("id") != organization_id:
                    continue
                project_id = project.get("projectId")
                if not project_id:
                    continue
                project_key = project.get(key_results_by)
                if not project_key:
                    raise ValueError(
                        f"Project '{project_id}' missing key '{key_results_by}'"
                    )
                if project_key in projects:
                    continue
                project = deepcopy(project)
                project["billingAccountID"] = billing_account_projects.get(project_id)
                projects[project_key] = project
            request = crm.projects().list_next(previous_request=request, previous_response=response)

        return projects

    def get_google_org_units(
        self,
        *,
        unhump_org_units: Optional[bool] = None,
        flatten_nested_org_units: Optional[bool] = None,
        use_basename: Optional[bool] = None,
        allowed_ou_types: Optional[Sequence[str]] = None,
        denied_ou_types: Optional[Sequence[str]] = None,
        include_root: Optional[bool] = None,
        domain: Optional[str] = None,
    ) -> dict[str, Any]:
        """Fetch organizational units using the Admin Directory API."""

        if unhump_org_units is None:
            unhump_org_units = self.get_input(
                "unhump_org_units", required=False, default=True, is_bool=True
            )
        if flatten_nested_org_units is None:
            flatten_nested_org_units = self.get_input(
                "flatten_nested_org_units", required=False, default=False, is_bool=True
            )
        if use_basename is None:
            use_basename = self.get_input(
                "use_basename", required=False, default=False, is_bool=True
            )
        if allowed_ou_types is None:
            allowed_ou_types = self.decode_input(
                "allowed_ou_types",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )
        if denied_ou_types is None:
            denied_ou_types = self.decode_input(
                "denied_ou_types",
                required=False,
                default=[],
                decode_from_base64=False,
                allow_none=False,
            )
        if include_root is None:
            include_root = self.get_input(
                "include_root", required=False, default=True, is_bool=True
            )
        if domain is None:
            domain = self.get_input("google_domain", required=False) or DEFAULT_DOMAIN

        directory = self.get_admin_directory_service()
        org_units: dict[str, Any] = {}

        def fetch_org_units(org_unit_path: str = "/") -> None:
            params = {"type": "all", "customerId": "my_customer"}
            if org_unit_path != "/":
                params["orgUnitPath"] = org_unit_path
            if domain:
                params["domain"] = domain

            response = directory.orgunits().list(**params).execute()
            for org_unit in response.get("organizationUnits", []):
                path = org_unit.get("orgUnitPath") or "/"
                name = Path(path).name.lower()

                if not include_root and path == "/":
                    continue
                if allowed_ou_types and name not in allowed_ou_types:
                    continue
                if denied_ou_types and name in denied_ou_types:
                    continue

                org_units[path] = org_unit
                fetch_org_units(path)

        fetch_org_units()

        if flatten_nested_org_units:
            org_units = self._flatten_org_unit_hierarchy(
                org_units,
                use_basename=use_basename,
            )

        if unhump_org_units:
            return {Path(k).as_posix(): unhump_map(v) for k, v in org_units.items()}
        return org_units

    def _flatten_org_unit_hierarchy(
        self,
        org_units: Mapping[str, Any],
        *,
        use_basename: bool = False,
    ) -> dict[str, Any]:
        """Flatten org units and nest children under a `units` key."""

        def get_basename(path: str) -> str:
            if path == "/":
                return "root"
            return Path(path).name.lower()

        def get_display_key(path: str) -> str:
            return get_basename(path) if use_basename else path.lower()

        def build_hierarchy(parent_path: str, all_units: Mapping[str, Any]) -> dict[str, Any]:
            children: dict[str, Any] = {}
            for ou_path, ou_data in all_units.items():
                if ou_data.get("parentOrgUnitPath") == parent_path:
                    clean_data = {
                        key: value
                        for key, value in ou_data.items()
                        if key not in ["etag", "kind", "orgUnitPath"]
                    }
                    nested = build_hierarchy(ou_path, all_units)
                    if nested:
                        clean_data["units"] = nested
                    children[get_display_key(ou_path)] = clean_data
            return children

        flattened: dict[str, Any] = {}
        for ou_path, ou_data in org_units.items():
            if ou_data.get("parentOrgUnitPath") == "/":
                clean_data = {
                    key: value
                    for key, value in ou_data.items()
                    if key not in ["etag", "kind", "orgUnitPath"]
                }
                nested = build_hierarchy(ou_path, org_units)
                if nested:
                    clean_data["units"] = nested
                flattened[get_display_key(ou_path)] = clean_data
        return flattened

    def _get_checkable_resources(self) -> dict[str, Any]:
        """Return the mapping of APIs to resource checks and usage hints."""

        return {
            "compute.googleapis.com": {
                "name": "Compute Engine",
                "indicates_usage": True,
                "enables_checks": [
                    "compute.googleapis.com/Address",
                    "compute.googleapis.com/Autoscaler",
                    "compute.googleapis.com/BackendService",
                    "compute.googleapis.com/Disk",
                    "compute.googleapis.com/Firewall",
                    "compute.googleapis.com/ForwardingRule",
                    "compute.googleapis.com/HealthCheck",
                    "compute.googleapis.com/Instance",
                    "compute.googleapis.com/InstanceGroup",
                    "compute.googleapis.com/InstanceGroupManager",
                    "compute.googleapis.com/InstanceTemplate",
                    "compute.googleapis.com/Network",
                    "compute.googleapis.com/Router",
                    "compute.googleapis.com/Snapshot",
                    "compute.googleapis.com/SslCertificate",
                    "compute.googleapis.com/Subnetwork",
                    "compute.googleapis.com/TargetHttpProxy",
                    "compute.googleapis.com/TargetHttpsProxy",
                    "compute.googleapis.com/TargetPool",
                    "compute.googleapis.com/UrlMap",
                ],
            },
            "container.googleapis.com": {
                "name": "Google Kubernetes Engine",
                "indicates_usage": True,
                "enables_checks": [
                    "container.googleapis.com/Cluster",
                    "container.googleapis.com/NodePool",
                ],
            },
            "cloudfunctions.googleapis.com": {
                "name": "Cloud Functions",
                "indicates_usage": True,
                "enables_checks": ["cloudfunctions.googleapis.com/CloudFunction"],
            },
            "run.googleapis.com": {
                "name": "Cloud Run",
                "indicates_usage": True,
                "enables_checks": [
                    "run.googleapis.com/Service",
                    "run.googleapis.com/Revision",
                ],
            },
            "workflows.googleapis.com": {
                "name": "Cloud Workflows",
                "indicates_usage": True,
                "enables_checks": ["workflows.googleapis.com/Workflow"],
            },
            "sqladmin.googleapis.com": {
                "name": "Cloud SQL",
                "indicates_usage": True,
                "enables_checks": ["sqladmin.googleapis.com/Instance"],
            },
            "bigquery.googleapis.com": {
                "name": "BigQuery",
                "indicates_usage": False,
                "enables_checks": [
                    "bigquery.googleapis.com/Dataset",
                    "bigquery.googleapis.com/Table",
                    "bigquery.googleapis.com/Model",
                ],
            },
            "storage.googleapis.com": {
                "name": "Cloud Storage",
                "indicates_usage": False,
                "enables_checks": ["storage.googleapis.com/Bucket"],
            },
            "redis.googleapis.com": {
                "name": "Redis",
                "indicates_usage": True,
                "enables_checks": ["redis.googleapis.com/Instance"],
            },
            "memcache.googleapis.com": {
                "name": "Memorystore for Memcached",
                "indicates_usage": True,
                "enables_checks": ["memcache.googleapis.com/Instance"],
            },
            "filestore.googleapis.com": {
                "name": "Filestore",
                "indicates_usage": True,
                "enables_checks": ["file.googleapis.com/Instance"],
            },
            "secretmanager.googleapis.com": {
                "name": "Secret Manager",
                "indicates_usage": True,
                "enables_checks": ["secretmanager.googleapis.com/Secret"],
            },
            "cloudkms.googleapis.com": {
                "name": "Cloud KMS",
                "indicates_usage": True,
                "enables_checks": [
                    "cloudkms.googleapis.com/CryptoKey",
                    "cloudkms.googleapis.com/KeyRing",
                ],
            },
            "iam.googleapis.com": {
                "name": "Identity and Access Management",
                "indicates_usage": False,
                "enables_checks": [
                    "iam.googleapis.com/Role",
                    "iam.googleapis.com/ServiceAccount",
                    "iam.googleapis.com/ServiceAccountKey",
                ],
            },
            "artifactregistry.googleapis.com": {
                "name": "Artifact Registry",
                "indicates_usage": True,
                "enables_checks": [
                    "artifactregistry.googleapis.com/Repository",
                    "artifactregistry.googleapis.com/DockerImage",
                ],
            },
            "cloudbuild.googleapis.com": {
                "name": "Cloud Build",
                "indicates_usage": True,
                "enables_checks": [
                    "cloudbuild.googleapis.com/Trigger",
                    "cloudbuild.googleapis.com/WorkerPool",
                ],
            },
            "servicenetworking.googleapis.com": {
                "name": "Service Networking",
                "indicates_usage": True,
                "enables_checks": ["servicenetworking.googleapis.com/Connection"],
            },
            "vpcaccess.googleapis.com": {
                "name": "VPC Access",
                "indicates_usage": True,
                "enables_checks": ["vpcaccess.googleapis.com/Connector"],
            },
            "dns.googleapis.com": {
                "name": "Cloud DNS",
                "indicates_usage": True,
                "enables_checks": [
                    "dns.googleapis.com/ManagedZone",
                    "dns.googleapis.com/Policy",
                ],
            },
            "networksecurity.googleapis.com": {
                "name": "Network Security",
                "indicates_usage": True,
                "enables_checks": [
                    "networksecurity.googleapis.com/ClientTlsPolicy",
                    "networksecurity.googleapis.com/ServerTlsPolicy",
                ],
            },
            "pubsub.googleapis.com": {
                "name": "Pub/Sub",
                "indicates_usage": True,
                "enables_checks": [
                    "pubsub.googleapis.com/Topic",
                    "pubsub.googleapis.com/Subscription",
                ],
            },
            "cloudscheduler.googleapis.com": {
                "name": "Cloud Scheduler",
                "indicates_usage": True,
                "enables_checks": ["cloudscheduler.googleapis.com/Job"],
            },
            "cloudtasks.googleapis.com": {
                "name": "Cloud Tasks",
                "indicates_usage": True,
                "enables_checks": ["cloudtasks.googleapis.com/Queue"],
            },
            "dataflow.googleapis.com": {
                "name": "Dataflow",
                "indicates_usage": True,
                "enables_checks": [
                    "dataflow.googleapis.com/Job",
                    "dataflow.googleapis.com/Snapshot",
                ],
            },
            "dataproc.googleapis.com": {
                "name": "Dataproc",
                "indicates_usage": True,
                "enables_checks": [
                    "dataproc.googleapis.com/Cluster",
                    "dataproc.googleapis.com/WorkflowTemplate",
                ],
            },
            "monitoring.googleapis.com": {
                "name": "Cloud Monitoring",
                "indicates_usage": False,
                "enables_checks": [
                    "monitoring.googleapis.com/AlertPolicy",
                    "monitoring.googleapis.com/Group",
                    "monitoring.googleapis.com/NotificationChannel",
                ],
            },
            "logging.googleapis.com": {
                "name": "Cloud Logging",
                "indicates_usage": False,
                "enables_checks": [
                    "logging.googleapis.com/LogMetric",
                    "logging.googleapis.com/LogSink",
                    "logging.googleapis.com/LogBucket",
                ],
            },
            "cloudapis.googleapis.com": {
                "name": "Google Cloud APIs",
                "indicates_usage": False,
                "enables_checks": ["cloudapis.googleapis.com/ApiKey"],
            },
            "serviceusage.googleapis.com": {
                "name": "Service Usage",
                "indicates_usage": False,
                "enables_checks": [],
            },
        }

    def _convert_to_log_resource_types(self, cloud_asset_types: Sequence[str]) -> list[str]:
        """Convert Cloud Asset resource types to Logging resource identifiers."""

        log_resource_types: list[str] = []
        for resource_type in cloud_asset_types:
            if "compute.googleapis.com/" in resource_type:
                log_resource_types.append(f"gce_{resource_type.split('/')[-1].lower()}")
            elif "container.googleapis.com/" in resource_type:
                log_resource_types.append(f"k8s_{resource_type.split('/')[-1].lower()}")
            elif "cloudfunctions.googleapis.com/" in resource_type:
                log_resource_types.append("cloudfunctions_function")
            elif "run.googleapis.com/" in resource_type:
                log_resource_types.append("cloud_run_revision")
            elif "bigquery.googleapis.com/" in resource_type:
                log_resource_types.append(f"bigquery_{resource_type.split('/')[-1].lower()}")
            elif "storage.googleapis.com/" in resource_type:
                log_resource_types.append("gcs_bucket")
            else:
                log_resource_types.append(resource_type.split("/")[-1].lower())
        return log_resource_types

    def _log_entries(self, entries: Sequence[Mapping[str, Any]]) -> None:
        """Log a concise summary of log entries."""

        for entry in entries:
            resource_type = entry.get("resource", {}).get("type", "unknown resource type")
            timestamp = entry.get("timestamp", "no timestamp")
            severity = entry.get("severity", "unknown severity")
            service = entry.get("protoPayload", {}).get("serviceName", "unknown service")
            operation = entry.get("protoPayload", {}).get("methodName", "unknown method")
            self.logger.info(
                "  Entry:\n"
                f"    Timestamp: {timestamp}\n"
                f"    Resource Type: {resource_type}\n"
                f"    Service: {service}\n"
                f"    Severity: {severity}\n"
                f"    Operation: {operation}"
            )

    def _check_project_resources(
        self,
        google_client: "GoogleConnector",
        project_id: str,
        enabled_api_names: set[str],
        checkable_resource_types: Sequence[str],
    ) -> Optional[bool]:
        """Use the Cloud Asset API to detect provisioned resources."""

        if "cloudasset.googleapis.com" not in enabled_api_names or not checkable_resource_types:
            return None

        try:
            asset_service = google_client.get_service("cloudasset", "v1")
            request = asset_service.assets().list(
                parent=f"projects/{project_id}",
                contentType="RESOURCE",
                assetTypes=list(checkable_resource_types),
                pageSize=10,
            )
            response = request.execute()
            if response.get("assets"):
                self.logger.info("Found active resources using Cloud Asset API.")
                for asset in response.get("assets", [])[:5]:
                    self.logger.info(f"  Resource Type: {asset.get('assetType')}")
                return True
            return False
        except Exception as exc:
            self.logger.error(f"Error checking Cloud Asset inventory: {exc}")
            return None

    def _check_project_logs(
        self,
        google_client: "GoogleConnector",
        project_id: str,
        checkable_resource_types: Sequence[str],
    ) -> Optional[bool]:
        """Search project-level logs for recent activity."""

        try:
            logging_service = google_client.get_service("logging", "v2")
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
            log_resource_types = self._convert_to_log_resource_types(checkable_resource_types)
            if not log_resource_types:
                return False

            resource_filter = " OR ".join(
                f'resource.type="{rtype}"' for rtype in log_resource_types
            )
            log_filter = (
                f'timestamp >= "{thirty_days_ago}" '
                'AND NOT protoPayload.methodName:("get" OR "list") '
                'AND NOT resource.type="project" '
                f"AND ({resource_filter})"
            )
            self.logger.info(f"Using log filter:\n{log_filter}")

            response = logging_service.entries().list(
                body={
                    "resourceNames": [f"projects/{project_id}"],
                    "filter": log_filter,
                    "pageSize": 10,
                }
            ).execute()

            if response.get("entries"):
                self._log_entries(response.get("entries")[:5])
                return True
            return False
        except Exception as exc:
            self.logger.error(f"Error checking project-level logs: {exc}")
            return None

    def _check_org_level_billing(
        self,
        google_client: "GoogleConnector",
        project_id: str,
    ) -> Optional[bool]:
        """Return True if billing is enabled for the project."""

        try:
            cloud_billing = google_client.get_service("cloudbilling", "v1")
            billing_info = (
                cloud_billing.projects()
                .getBillingInfo(name=f"projects/{project_id}")
                .execute()
            )
            if billing_info.get("billingEnabled"):
                self.logger.info("Project billing is enabled.")
                return True
            return False
        except Exception as exc:
            self.logger.debug(f"Could not check billing info: {exc}")
            return None

    def _check_org_level_iam(
        self,
        google_client: "GoogleConnector",
        project_id: str,
        current_service_account_email: Optional[str],
    ) -> Optional[bool]:
        """Return True if IAM bindings exist beyond the current service account."""

        try:
            resource_manager = google_client.get_service("cloudresourcemanager", "v3")
            policy = resource_manager.projects().getIamPolicy(
                resource=f"projects/{project_id}",
                body={
                    "options": {
                        "requestedPolicyVersion": 3,
                        "includeInheritedRoles": True,
                    }
                },
            ).execute()

            for binding in policy.get("bindings", []):
                role = binding.get("role", "unknown")
                for member in binding.get("members", []):
                    if current_service_account_email and member == f"serviceAccount:{current_service_account_email}":
                        continue
                    self.logger.info(
                        f"Found IAM binding indicating usage - Role: {role}, Member: {member}"
                    )
                    return True
            return False
        except Exception as exc:
            self.logger.debug(f"Could not inspect IAM bindings: {exc}")
            return None

    def _check_org_level_logs(
        self,
        google_client: "GoogleConnector",
        project_id: str,
        organization_id: str,
    ) -> Optional[bool]:
        """Return True when organization-level logs show project activity."""

        try:
            logging_service = google_client.get_service("logging", "v2")
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
            log_filter = f"""
                resource.labels.project_id="{project_id}"
                AND timestamp >= "{thirty_days_ago}"
                AND NOT protoPayload.methodName:("get" OR "list")
                AND (
                    resource.type=("gce_network" OR "gce_firewall" OR "gce_route" OR "dns_managed_zone")
                    OR protoPayload.serviceName=("compute.googleapis.com" OR "container.googleapis.com"
                        OR "cloudresourcemanager.googleapis.com")
                    OR protoPayload.methodName:("CreateService" OR "DeleteService" OR "UpdateService")
                    OR severity=("ERROR" OR "CRITICAL")
                )
            """

            response = logging_service.entries().list(
                body={
                    "resourceNames": [f"organizations/{organization_id}"],
                    "filter": log_filter,
                    "pageSize": 10,
                }
            ).execute()

            if response.get("entries"):
                self._log_entries(response.get("entries")[:5])
                return True
            return False
        except Exception as exc:
            self.logger.error(f"Error checking organization-level logs: {exc}")
            return None

    def is_google_project_empty(
        self,
        project_id: Optional[str] = None,
        *,
        organization_id: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> bool:
        """Best-effort determination of whether a project contains resources."""

        project_id = project_id or self.get_input("project_id", required=True)
        client = self._with_overrides(service_account_info=service_account_info)

        if not organization_id:
            organization_id = self.get_google_organization_id(
                service_account_info=service_account_info,
            )

        current_service_account_email = client.subject

        try:
            billing_result = self._check_org_level_billing(client, project_id)
            if billing_result is True:
                return False

            iam_result = self._check_org_level_iam(
                client,
                project_id,
                current_service_account_email,
            )
            if iam_result is True:
                return False

            log_result = self._check_org_level_logs(client, project_id, organization_id)
            if log_result is True:
                return False

            enabled_apis = self.get_enabled_apis_for_google_project(
                project_id=project_id,
                service_account_info=service_account_info,
            )
            enabled_api_names = {api.get("name", "").split("/")[-1] for api in enabled_apis}

            if not enabled_api_names:
                self.logger.info(
                    f"Project '{project_id}' has no enabled APIs. Treating as empty."
                )
                return True

            checkable_resources = self._get_checkable_resources()
            usage_indicating_apis = {
                api
                for api, info in checkable_resources.items()
                if api in enabled_api_names and info["indicates_usage"]
            }
            if usage_indicating_apis:
                self.logger.info(
                    "Project has APIs enabled that indicate usage: "
                    + ", ".join(checkable_resources[api]["name"] for api in usage_indicating_apis)
                )
                return False

            checkable_resource_types: list[str] = []
            for api in enabled_api_names:
                resource_info = checkable_resources.get(api)
                if resource_info:
                    checkable_resource_types.extend(resource_info["enables_checks"])

            if not checkable_resource_types:
                self.logger.info(
                    "No APIs enabled that allow deeper inspection. Treating project as empty."
                )
                return True

            resource_result = self._check_project_resources(
                client,
                project_id,
                enabled_api_names,
                checkable_resource_types,
            )
            if resource_result is True:
                return False

            log_result = self._check_project_logs(
                client,
                project_id,
                checkable_resource_types,
            )
            if log_result is True:
                return False

            self.logger.info(
                f"No signals of activity detected for project '{project_id}'. Treating as empty."
            )
            return True
        except Exception as exc:
            self.logger.error(f"Error checking project '{project_id}': {exc}")
            return False

    # ------------------------------------------------------------------
    # Billing helpers
    # ------------------------------------------------------------------
    def link_google_billing_account(
        self,
        project_id: str,
        *,
        billing_account_id: Optional[str] = None,
        billing_account_name: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> None:
        """Assign a billing account to a project."""

        if not billing_account_id:
            billing_account_id = self.get_google_billing_account(
                billing_account_name or "Primary",
                service_account_info=service_account_info,
            )

        client = self._with_overrides(service_account_info=service_account_info)
        billing = client.get_service("cloudbilling", "v1")
        billing.projects().updateBillingInfo(
            name=f"projects/{project_id}",
            body={"billingAccountName": f"billingAccounts/{billing_account_id}"},
        ).execute()
        self.logger.info(
            f"Linked project '{project_id}' to billing account '{billing_account_id}'."
        )

    def move_google_projects_to_billing_account(
        self,
        *,
        billing_account_id: Optional[str] = None,
        billing_account_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
        delete_empty_projects: bool = True,
    ) -> dict[str, Any]:
        """Link all organization projects to a billing account, deleting empty ones."""

        if not billing_account_id:
            billing_account_id = self.get_google_billing_account(
                billing_account_name or "Primary",
                service_account_info=service_account_info,
            )

        projects = self.get_google_projects(
            organization_id=organization_id,
            service_account_info=service_account_info,
        )

        processed: dict[str, Any] = {}
        for project_id, project in projects.items():
            current_billing = project.get("billingAccountID")
            lifecycle_state = project.get("lifecycleState")

            if lifecycle_state != "ACTIVE":
                self.logger.info(
                    f"Skipping project '{project_id}' because lifecycle state is {lifecycle_state}."
                )
                continue

            if current_billing == billing_account_id:
                continue

            if delete_empty_projects and self.is_google_project_empty(
                project_id=project_id,
                organization_id=organization_id,
                service_account_info=service_account_info,
            ):
                self.logger.warning(
                    f"Deleting project '{project_id}' because it is empty and unlinked."
                )
                self.delete_empty_google_project(
                    project_id=project_id,
                    organization_id=organization_id,
                    service_account_info=service_account_info,
                )
                processed[project_id] = {"action": "deleted"}
                continue

            self.link_google_billing_account(
                project_id,
                billing_account_id=billing_account_id,
                service_account_info=service_account_info,
            )
            processed[project_id] = {"action": "linked", "billingAccountID": billing_account_id}

        return processed

    # ------------------------------------------------------------------
    # Service inventory helpers
    # ------------------------------------------------------------------
    def get_enabled_apis_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> list[dict[str, Any]]:
        """List enabled APIs via the Service Usage API."""

        client = self._with_overrides(service_account_info=service_account_info)
        service_usage = client.get_service("serviceusage", "v1")

        enabled: list[dict[str, Any]] = []
        request = service_usage.services().list(
            parent=f"projects/{project_id}",
            filter="state:ENABLED",
        )
        while request is not None:
            response = request.execute()
            enabled.extend(response.get("services", []))
            request = service_usage.services().list_next(
                previous_request=request,
                previous_response=response,
            )
        return enabled

    def get_storage_buckets_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return Cloud Storage buckets for the project keyed by bucket name."""

        client = self._with_overrides(service_account_info=service_account_info)
        storage = client.get_service("storage", "v1")

        buckets: dict[str, Any] = {}
        request = storage.buckets().list(project=project_id)
        while request is not None:
            response = request.execute()
            for bucket in response.get("items", []):
                name = bucket.get("name")
                if name:
                    buckets[name] = bucket
            request = storage.buckets().list_next(
                previous_request=request,
                previous_response=response,
            )
        return buckets

    def get_gke_clusters_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return GKE clusters for the project keyed by cluster name."""

        client = self._with_overrides(service_account_info=service_account_info)
        container = client.get_service("container", "v1")

        clusters: dict[str, Any] = {}
        response = container.projects().locations().clusters().list(
            parent=f"projects/{project_id}/locations/-"
        ).execute()
        for cluster in response.get("clusters", []):
            name = cluster.get("name")
            if name:
                clusters[name] = cluster
        return clusters

    def get_compute_instances_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return Compute Engine instances keyed by instance name."""

        client = self._with_overrides(service_account_info=service_account_info)
        compute = client.get_service("compute", "v1")

        instances: dict[str, Any] = {}
        zones = (
            compute.zones()
            .list(project=project_id)
            .execute()
            .get("items", [])
        )
        for zone in zones:
            zone_name = zone.get("name")
            if not zone_name:
                continue
            request = compute.instances().list(project=project_id, zone=zone_name)
            while request is not None:
                response = request.execute()
                for instance in response.get("items", []):
                    instance_name = instance.get("name")
                    if instance_name:
                        instances[instance_name] = instance
                request = compute.instances().list_next(
                    previous_request=request,
                    previous_response=response,
                )
        return instances

    def get_service_accounts_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return IAM service accounts keyed by email."""

        client = self._with_overrides(service_account_info=service_account_info)
        iam = client.get_service("iam", "v1")

        accounts: dict[str, Any] = {}
        request = iam.projects().serviceAccounts().list(name=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            for account in response.get("accounts", []):
                email = account.get("email")
                if email:
                    accounts[email] = account
            request = iam.projects().serviceAccounts().list_next(
                previous_request=request,
                previous_response=response,
            )
        return accounts

    def get_sql_instances_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return Cloud SQL instances keyed by instance name."""

        client = self._with_overrides(service_account_info=service_account_info)
        sqladmin = client.get_service("sqladmin", "v1")

        instances: dict[str, Any] = {}
        request = sqladmin.instances().list(project=project_id)
        while request is not None:
            response = request.execute()
            for instance in response.get("items", []):
                name = instance.get("name")
                if name:
                    instances[name] = instance
            request = sqladmin.instances().list_next(
                previous_request=request,
                previous_response=response,
            )
        return instances

    def get_pubsub_queues_for_google_project(
        self,
        project_id: str,
        *,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Return Pub/Sub topics and subscriptions keyed by resource name."""

        client = self._with_overrides(service_account_info=service_account_info)
        pubsub = client.get_service("pubsub", "v1")

        queues: dict[str, Any] = {}
        request = pubsub.projects().topics().list(project=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            for topic in response.get("topics", []):
                topic_name = topic.get("name")
                if topic_name:
                    queues[topic_name] = {"type": "topic", "details": topic}
            request = pubsub.projects().topics().list_next(
                previous_request=request,
                previous_response=response,
            )

        request = pubsub.projects().subscriptions().list(project=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            for subscription in response.get("subscriptions", []):
                sub_name = subscription.get("name")
                if sub_name:
                    queues[sub_name] = {"type": "subscription", "details": subscription}
            request = pubsub.projects().subscriptions().list_next(
                previous_request=request,
                previous_response=response,
            )
        return queues

    def enable_google_apis(
        self,
        project_id: str,
        *,
        apis: Optional[Sequence[str]] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, list[str]]:
        """Enable a set of APIs for the project."""

        apis = list(apis or GCP_REQUIRED_APIS)
        client = self._with_overrides(service_account_info=service_account_info)
        service_usage = client.get_service("serviceusage", "v1")

        enabled: list[str] = []
        failed: list[str] = []
        service_usage_disabled = False

        for api in apis:
            if api == "serviceusage.googleapis.com":
                self.logger.warning("serviceusage API cannot enable itself; skipping.")
                continue
            if service_usage_disabled:
                failed.append(api)
                continue
            try:
                service_usage.services().enable(
                    name=f"projects/{project_id}/services/{api}"
                ).execute()
                enabled.append(api)
            except HttpError as err:
                if err.resp.status == 409 or "has already been enabled" in str(err):
                    enabled.append(api)
                else:
                    failed.append(api)
                    if "serviceusage" in str(err).lower():
                        service_usage_disabled = True
            except Exception as exc:
                failed.append(api)
                self.logger.error(f"Failed to enable API '{api}': {exc}")

        return {"enabled": enabled, "failed": failed}

    def create_google_kms_key(
        self,
        project_id: str,
        *,
        kms_keyring_name: Optional[str] = None,
        kms_key_name: Optional[str] = None,
        region: str = "us-east1",
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> dict[str, Any]:
        """Create a KMS keyring and key if they do not already exist."""

        kms_keyring_name = kms_keyring_name or GCP_KMS["keyring_name"]
        kms_key_name = kms_key_name or GCP_KMS["key_name"]

        client = self._with_overrides(service_account_info=service_account_info)
        kms = client.get_service("cloudkms", "v1")

        keyring_parent = f"projects/{project_id}/locations/{region}"
        try:
            kms.projects().locations().keyRings().create(
                parent=keyring_parent,
                keyRingId=kms_keyring_name,
                body={},
            ).execute()
            self.logger.info(f"Created KMS keyring '{kms_keyring_name}'.")
        except HttpError as err:
            if err.resp.status != 409:
                raise
        crypto_parent = f"{keyring_parent}/keyRings/{kms_keyring_name}"
        try:
            kms.projects().locations().keyRings().cryptoKeys().create(
                parent=crypto_parent,
                cryptoKeyId=kms_key_name,
                body={"purpose": "ENCRYPT_DECRYPT"},
            ).execute()
            self.logger.info(f"Created KMS key '{kms_key_name}'.")
        except HttpError as err:
            if err.resp.status != 409:
                raise
        return {"keyring": kms_keyring_name, "key": kms_key_name, "region": region}

    # ------------------------------------------------------------------
    # Project + IAM mutations
    # ------------------------------------------------------------------
    def create_google_project(
        self,
        project_name: str,
        *,
        labels: Optional[Mapping[str, str]] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> str:
        """Create a project when it does not already exist, returning its ID."""

        labels = dict(labels or GCP_SECURITY_PROJECT["resource_labels"])
        client = self._with_overrides(service_account_info=service_account_info)
        crm = client.get_service("cloudresourcemanager", "v1")

        response = crm.projects().list(filter=f"name:{project_name}").execute()
        projects = response.get("projects", [])
        if projects:
            project_id = projects[0]["projectId"]
            current_labels = projects[0].get("labels", {})
            if current_labels != labels:
                crm.projects().update(
                    projectId=project_id,
                    body={"labels": labels},
                ).execute()
            return project_id

        project_id = project_name.lower().replace(" ", "-")
        create_response = crm.projects().create(
            body={
                "projectId": project_id,
                "name": project_name,
                "labels": labels,
            }
        ).execute()
        return create_response["projectId"]

    def delete_empty_google_project(
        self,
        project_id: str,
        *,
        organization_id: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> bool:
        """Delete a project when it is empty; returns True if deleted."""

        if not self.is_google_project_empty(
            project_id=project_id,
            organization_id=organization_id,
            service_account_info=service_account_info,
        ):
            self.logger.info(f"Project '{project_id}' is not empty; skipping deletion.")
            return False

        client = self._with_overrides(service_account_info=service_account_info)
        crm = client.get_service("cloudresourcemanager", "v1")
        crm.projects().delete(projectId=project_id).execute()
        self.logger.info(f"Deleted project '{project_id}'.")
        return True

    def assign_google_project_iam_roles(
        self,
        project_id: str,
        *,
        roles: Optional[Sequence[str]] = None,
        service_account_identifier: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> None:
        """Assign IAM roles within a project to the provided service account."""

        roles = list(roles or GCP_REQUIRED_ROLES)
        client = self._with_overrides(service_account_info=service_account_info)
        crm = client.get_service("cloudresourcemanager", "v1")

        if not service_account_identifier:
            if client.subject:
                service_account_identifier = client.subject
            else:
                raise ValueError("Service account identifier could not be resolved.")

        if not service_account_identifier.startswith("serviceAccount:"):
            service_account_identifier = f"serviceAccount:{service_account_identifier}"

        policy = crm.projects().getIamPolicy(
            resource=project_id,
            body={"options": {"requestedPolicyVersion": 3}},
        ).execute()

        bindings = policy.get("bindings", [])
        binding_map = {binding["role"]: binding for binding in bindings}

        for role in roles:
            binding = binding_map.get(role)
            if binding:
                members = binding.setdefault("members", [])
                if service_account_identifier not in members:
                    members.append(service_account_identifier)
            else:
                bindings.append(
                    {"role": role, "members": [service_account_identifier]}
                )

        policy["bindings"] = bindings
        crm.projects().setIamPolicy(
            resource=project_id,
            body={"policy": policy},
        ).execute()

    def assign_service_account_to_google_organization(
        self,
        organization_id: Optional[str] = None,
        *,
        roles: Optional[Sequence[str]] = None,
        service_account_email: Optional[str] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> None:
        """Assign IAM roles to a service account at the organization scope."""

        client = self._with_overrides(service_account_info=service_account_info)
        resource_manager = client.get_service("cloudresourcemanager", "v1")

        if not organization_id:
            organization_id = self.get_google_organization_id(
                service_account_info=service_account_info,
            )

        if not service_account_email:
            if client.subject:
                service_account_email = client.subject
            else:
                raise ValueError("Service account email could not be resolved.")

        if not service_account_email.startswith("serviceAccount:"):
            service_account_email = f"serviceAccount:{service_account_email}"

        roles = list(roles or GCP_REQUIRED_ORGANIZATION_ROLES)

        policy = resource_manager.organizations().getIamPolicy(
            resource=f"organizations/{organization_id}",
            body={},
        ).execute()
        bindings = policy.get("bindings", [])
        binding_map = {binding["role"]: binding for binding in bindings}

        for role in roles:
            binding = binding_map.get(role)
            if binding:
                members = binding.setdefault("members", [])
                if service_account_email not in members:
                    members.append(service_account_email)
            else:
                bindings.append(
                    {"role": role, "members": [service_account_email]}
                )

        policy["bindings"] = bindings
        resource_manager.organizations().setIamPolicy(
            resource=f"organizations/{organization_id}",
            body={"policy": policy},
        ).execute()

    def assign_service_account_to_google_project(
        self,
        project_id: str,
        *,
        service_account_email: Optional[str] = None,
        roles: Optional[Sequence[str]] = None,
        service_account_info: Optional[dict[str, Any] | str] = None,
    ) -> None:
        """Assign specific roles to a service account within a project."""

        roles = list(roles or GCP_REQUIRED_ROLES)
        client = self._with_overrides(service_account_info=service_account_info)

        if not service_account_email:
            if client.subject:
                service_account_email = client.subject
            else:
                raise ValueError("Service account email could not be resolved.")

        self.assign_google_project_iam_roles(
            project_id,
            roles=roles,
            service_account_identifier=service_account_email,
            service_account_info=service_account_info,
        )
