"""Google Workspace (Admin Directory) operations.

This module provides operations for managing Google Workspace users and groups
through the Admin Directory API.
"""

from __future__ import annotations

from typing import Any, Optional

from extended_data_types import unhump_map


class GoogleWorkspaceMixin:
    """Mixin providing Google Workspace operations.

    This mixin requires the base GoogleConnector class to provide:
    - get_admin_directory_service()
    - get_service()
    - logger
    """

    def list_users(
        self,
        domain: Optional[str] = None,
        max_results: int = 500,
        unhump_users: bool = False,
        subject: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List users from Google Workspace.

        Args:
            domain: Optional domain to filter users.
            max_results: Maximum results per page. Defaults to 500.
            unhump_users: Convert keys to snake_case. Defaults to False.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            List of user dictionaries.
        """
        service = self.get_admin_directory_service(subject=subject)
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

        if unhump_users:
            users = [unhump_map(u) for u in users]

        return users

    def get_user(
        self,
        user_key: str,
        subject: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Get a specific user from Google Workspace.

        Args:
            user_key: Email or unique ID of the user.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            User dictionary or None if not found.
        """
        from googleapiclient.errors import HttpError

        service = self.get_admin_directory_service(subject=subject)

        try:
            user = service.users().get(userKey=user_key).execute()
            return user
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"User not found: {user_key}")
                return None
            raise

    def create_user(
        self,
        primary_email: str,
        given_name: str,
        family_name: str,
        password: Optional[str] = None,
        change_password_at_next_login: bool = True,
        org_unit_path: str = "/",
        subject: Optional[str] = None,
        **additional_fields,
    ) -> dict[str, Any]:
        """Create a user in Google Workspace.

        Args:
            primary_email: Primary email address.
            given_name: First name.
            family_name: Last name.
            password: Initial password. Generated if not provided.
            change_password_at_next_login: Force password change. Defaults to True.
            org_unit_path: Organizational unit path. Defaults to '/'.
            subject: Email to impersonate for domain-wide delegation.
            **additional_fields: Additional user fields.

        Returns:
            Created user dictionary.
        """
        import secrets

        service = self.get_admin_directory_service(subject=subject)

        if not password:
            password = secrets.token_urlsafe(16)

        user_body = {
            "primaryEmail": primary_email,
            "name": {
                "givenName": given_name,
                "familyName": family_name,
            },
            "password": password,
            "changePasswordAtNextLogin": change_password_at_next_login,
            "orgUnitPath": org_unit_path,
            **additional_fields,
        }

        result = service.users().insert(body=user_body).execute()
        self.logger.info(f"Created user: {primary_email}")
        return result

    def update_user(
        self,
        user_key: str,
        subject: Optional[str] = None,
        **fields,
    ) -> dict[str, Any]:
        """Update a user in Google Workspace.

        Args:
            user_key: Email or unique ID of the user.
            subject: Email to impersonate for domain-wide delegation.
            **fields: Fields to update.

        Returns:
            Updated user dictionary.
        """
        service = self.get_admin_directory_service(subject=subject)
        result = service.users().update(userKey=user_key, body=fields).execute()
        self.logger.info(f"Updated user: {user_key}")
        return result

    def delete_user(
        self,
        user_key: str,
        subject: Optional[str] = None,
    ) -> None:
        """Delete a user from Google Workspace.

        Args:
            user_key: Email or unique ID of the user.
            subject: Email to impersonate for domain-wide delegation.
        """
        service = self.get_admin_directory_service(subject=subject)
        service.users().delete(userKey=user_key).execute()
        self.logger.info(f"Deleted user: {user_key}")

    def list_groups(
        self,
        domain: Optional[str] = None,
        max_results: int = 200,
        unhump_groups: bool = False,
        subject: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List groups from Google Workspace.

        Args:
            domain: Optional domain to filter groups.
            max_results: Maximum results per page. Defaults to 200.
            unhump_groups: Convert keys to snake_case. Defaults to False.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            List of group dictionaries.
        """
        service = self.get_admin_directory_service(subject=subject)
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

        if unhump_groups:
            groups = [unhump_map(g) for g in groups]

        return groups

    def get_group(
        self,
        group_key: str,
        subject: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Get a specific group from Google Workspace.

        Args:
            group_key: Email or unique ID of the group.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            Group dictionary or None if not found.
        """
        from googleapiclient.errors import HttpError

        service = self.get_admin_directory_service(subject=subject)

        try:
            group = service.groups().get(groupKey=group_key).execute()
            return group
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"Group not found: {group_key}")
                return None
            raise

    def create_group(
        self,
        email: str,
        name: str,
        description: str = "",
        subject: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a group in Google Workspace.

        Args:
            email: Group email address.
            name: Display name.
            description: Group description.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            Created group dictionary.
        """
        service = self.get_admin_directory_service(subject=subject)

        group_body = {
            "email": email,
            "name": name,
            "description": description,
        }

        result = service.groups().insert(body=group_body).execute()
        self.logger.info(f"Created group: {email}")
        return result

    def delete_group(
        self,
        group_key: str,
        subject: Optional[str] = None,
    ) -> None:
        """Delete a group from Google Workspace.

        Args:
            group_key: Email or unique ID of the group.
            subject: Email to impersonate for domain-wide delegation.
        """
        service = self.get_admin_directory_service(subject=subject)
        service.groups().delete(groupKey=group_key).execute()
        self.logger.info(f"Deleted group: {group_key}")

    def list_group_members(
        self,
        group_key: str,
        roles: Optional[list[str]] = None,
        unhump_members: bool = False,
        subject: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List members of a Google Workspace group.

        Args:
            group_key: Email or unique ID of the group.
            roles: Filter by roles (OWNER, MANAGER, MEMBER). Defaults to all.
            unhump_members: Convert keys to snake_case. Defaults to False.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            List of member dictionaries.
        """
        service = self.get_admin_directory_service(subject=subject)
        members: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"groupKey": group_key}
            if roles:
                params["roles"] = ",".join(roles)
            if page_token:
                params["pageToken"] = page_token

            response = service.members().list(**params).execute()
            members.extend(response.get("members", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(members)} members from group {group_key}")

        if unhump_members:
            members = [unhump_map(m) for m in members]

        return members

    def add_group_member(
        self,
        group_key: str,
        email: str,
        role: str = "MEMBER",
        subject: Optional[str] = None,
    ) -> dict[str, Any]:
        """Add a member to a Google Workspace group.

        Args:
            group_key: Email or unique ID of the group.
            email: Email of the member to add.
            role: Member role (OWNER, MANAGER, MEMBER). Defaults to MEMBER.
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            Created member dictionary.
        """
        service = self.get_admin_directory_service(subject=subject)

        member_body = {
            "email": email,
            "role": role,
        }

        result = service.members().insert(groupKey=group_key, body=member_body).execute()
        self.logger.info(f"Added {email} to group {group_key} with role {role}")
        return result

    def remove_group_member(
        self,
        group_key: str,
        member_key: str,
        subject: Optional[str] = None,
    ) -> None:
        """Remove a member from a Google Workspace group.

        Args:
            group_key: Email or unique ID of the group.
            member_key: Email or unique ID of the member.
            subject: Email to impersonate for domain-wide delegation.
        """
        service = self.get_admin_directory_service(subject=subject)
        service.members().delete(groupKey=group_key, memberKey=member_key).execute()
        self.logger.info(f"Removed {member_key} from group {group_key}")

    def list_org_units(
        self,
        org_unit_path: str = "/",
        org_unit_type: str = "all",
        subject: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List organizational units in Google Workspace.

        Args:
            org_unit_path: Parent org unit path. Defaults to '/'.
            org_unit_type: Type filter (all, children, allIncludingParent).
            subject: Email to impersonate for domain-wide delegation.

        Returns:
            List of org unit dictionaries.
        """
        service = self.get_admin_directory_service(subject=subject)

        response = (
            service.orgunits()
            .list(
                customerId="my_customer",
                orgUnitPath=org_unit_path,
                type=org_unit_type,
            )
            .execute()
        )

        org_units = response.get("organizationUnits", [])
        self.logger.info(f"Retrieved {len(org_units)} org units")
        return org_units

    def create_or_update_user(
        self,
        primary_email: str,
        given_name: str,
        family_name: str,
        password: Optional[str] = None,
        update_if_exists: bool = False,
        change_password_at_next_login: bool = True,
        org_unit_path: str = "/",
        subject: Optional[str] = None,
        **additional_fields,
    ) -> dict[str, Any]:
        """Create or update a user in Google Workspace.

        This method provides terraform-style idempotent user management.
        If update_if_exists is True and the user exists, it updates instead of failing.

        Args:
            primary_email: Primary email address.
            given_name: First name.
            family_name: Last name.
            password: Initial password. Generated if not provided.
            update_if_exists: If True, update existing user instead of failing.
            change_password_at_next_login: Force password change. Defaults to True.
            org_unit_path: Organizational unit path. Defaults to '/'.
            subject: Email to impersonate for domain-wide delegation.
            **additional_fields: Additional user fields.

        Returns:
            Created or updated user dictionary.
        """
        import secrets

        from googleapiclient.errors import HttpError

        service = self.get_admin_directory_service(subject=subject)

        if not password:
            password = secrets.token_urlsafe(16)

        user_body: dict[str, Any] = {
            "primaryEmail": primary_email,
            "name": {
                "givenName": given_name,
                "familyName": family_name,
            },
            "password": password,
            "changePasswordAtNextLogin": change_password_at_next_login,
            "orgUnitPath": org_unit_path,
            **additional_fields,
        }

        # Check if user exists
        try:
            existing = service.users().get(userKey=primary_email).execute()
            if update_if_exists:
                # Update existing user
                result = service.users().update(userKey=primary_email, body=user_body).execute()
                self.logger.info(f"Updated existing user: {primary_email}")
                return result
            self.logger.info(f"User already exists: {primary_email}")
            return existing
        except HttpError as e:
            if e.resp.status != 404:
                raise
            # User doesn't exist, create new

        result = service.users().insert(body=user_body).execute()
        self.logger.info(f"Created user: {primary_email}")
        return result

    def create_or_update_group(
        self,
        email: str,
        name: str,
        description: str = "",
        update_if_exists: bool = False,
        subject: Optional[str] = None,
        **additional_fields,
    ) -> dict[str, Any]:
        """Create or update a group in Google Workspace.

        This method provides terraform-style idempotent group management.
        If update_if_exists is True and the group exists, it updates instead of failing.

        Args:
            email: Group email address.
            name: Display name.
            description: Group description.
            update_if_exists: If True, update existing group instead of failing.
            subject: Email to impersonate for domain-wide delegation.
            **additional_fields: Additional group fields.

        Returns:
            Created or updated group dictionary.
        """
        from googleapiclient.errors import HttpError

        service = self.get_admin_directory_service(subject=subject)

        group_body: dict[str, Any] = {
            "email": email,
            "name": name,
            "description": description,
            **additional_fields,
        }

        # Check if group exists
        try:
            existing = service.groups().get(groupKey=email).execute()
            if update_if_exists:
                # Update existing group
                result = service.groups().update(groupKey=email, body=group_body).execute()
                self.logger.info(f"Updated existing group: {email}")
                return result
            self.logger.info(f"Group already exists: {email}")
            return existing
        except HttpError as e:
            if e.resp.status != 404:
                raise
            # Group doesn't exist, create new

        result = service.groups().insert(body=group_body).execute()
        self.logger.info(f"Created group: {email}")
        return result
