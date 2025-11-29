"""AWS IAM Identity Center (SSO) operations.

This module provides operations for managing AWS SSO users and groups
through IAM Identity Center.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from extended_data_types import unhump_map

if TYPE_CHECKING:
    pass


class AWSSSOixin:
    """Mixin providing AWS SSO/Identity Center operations.

    This mixin requires the base AWSConnector class to provide:
    - get_aws_client()
    - logger
    - execution_role_arn
    """

    def get_identity_store_id(
        self,
        execution_role_arn: Optional[str] = None,
    ) -> str:
        """Get the IAM Identity Center identity store ID.

        Args:
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The identity store ID.

        Raises:
            RuntimeError: If no SSO instance found.
        """
        self.logger.info("Getting IAM Identity Center identity store ID")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        sso_admin = self.get_aws_client(
            client_name="sso-admin",
            execution_role_arn=role_arn,
        )

        instances = sso_admin.list_instances()
        instance_list = instances.get("Instances", [])

        if not instance_list:
            raise RuntimeError("No SSO instances found")

        identity_store_id = instance_list[0]["IdentityStoreId"]
        self.logger.info(f"Identity store ID: {identity_store_id}")
        return identity_store_id

    def get_sso_instance_arn(
        self,
        execution_role_arn: Optional[str] = None,
    ) -> str:
        """Get the IAM Identity Center instance ARN.

        Args:
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            The SSO instance ARN.

        Raises:
            RuntimeError: If no SSO instance found.
        """
        self.logger.info("Getting IAM Identity Center instance ARN")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        sso_admin = self.get_aws_client(
            client_name="sso-admin",
            execution_role_arn=role_arn,
        )

        instances = sso_admin.list_instances()
        instance_list = instances.get("Instances", [])

        if not instance_list:
            raise RuntimeError("No SSO instances found")

        instance_arn = instance_list[0]["InstanceArn"]
        self.logger.info(f"SSO instance ARN: {instance_arn}")
        return instance_arn

    def list_sso_users(
        self,
        identity_store_id: Optional[str] = None,
        unhump_users: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """List all users from IAM Identity Center.

        Args:
            identity_store_id: Identity store ID. Auto-detected if not provided.
            unhump_users: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping user IDs to user data.
        """
        self.logger.info("Listing SSO users")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        if not identity_store_id:
            identity_store_id = self.get_identity_store_id(execution_role_arn=role_arn)

        identitystore = self.get_aws_client(
            client_name="identitystore",
            execution_role_arn=role_arn,
        )

        users: dict[str, dict[str, Any]] = {}
        paginator = identitystore.get_paginator("list_users")

        for page in paginator.paginate(IdentityStoreId=identity_store_id):
            for user in page.get("Users", []):
                user_id = user["UserId"]
                users[user_id] = user

        if unhump_users:
            users = {k: unhump_map(v) for k, v in users.items()}

        self.logger.info(f"Retrieved {len(users)} SSO users")
        return users

    def list_sso_groups(
        self,
        identity_store_id: Optional[str] = None,
        unhump_groups: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """List all groups from IAM Identity Center.

        Args:
            identity_store_id: Identity store ID. Auto-detected if not provided.
            unhump_groups: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping group IDs to group data.
        """
        self.logger.info("Listing SSO groups")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        if not identity_store_id:
            identity_store_id = self.get_identity_store_id(execution_role_arn=role_arn)

        identitystore = self.get_aws_client(
            client_name="identitystore",
            execution_role_arn=role_arn,
        )

        groups: dict[str, dict[str, Any]] = {}
        paginator = identitystore.get_paginator("list_groups")

        for page in paginator.paginate(IdentityStoreId=identity_store_id):
            for group in page.get("Groups", []):
                group_id = group["GroupId"]
                groups[group_id] = group

        if unhump_groups:
            groups = {k: unhump_map(v) for k, v in groups.items()}

        self.logger.info(f"Retrieved {len(groups)} SSO groups")
        return groups

    def get_sso_group_memberships(
        self,
        group_id: str,
        identity_store_id: Optional[str] = None,
        unhump_memberships: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get memberships for a specific SSO group.

        Args:
            group_id: The group ID to get memberships for.
            identity_store_id: Identity store ID. Auto-detected if not provided.
            unhump_memberships: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            List of membership records.
        """
        self.logger.info(f"Getting memberships for group {group_id}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        if not identity_store_id:
            identity_store_id = self.get_identity_store_id(execution_role_arn=role_arn)

        identitystore = self.get_aws_client(
            client_name="identitystore",
            execution_role_arn=role_arn,
        )

        memberships: list[dict[str, Any]] = []
        paginator = identitystore.get_paginator("list_group_memberships")

        for page in paginator.paginate(
            IdentityStoreId=identity_store_id,
            GroupId=group_id
        ):
            for membership in page.get("GroupMemberships", []):
                memberships.append(membership)

        if unhump_memberships:
            memberships = [unhump_map(m) for m in memberships]

        self.logger.info(f"Retrieved {len(memberships)} memberships for group {group_id}")
        return memberships

    def list_permission_sets(
        self,
        instance_arn: Optional[str] = None,
        unhump_sets: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """List all permission sets from IAM Identity Center.

        Args:
            instance_arn: SSO instance ARN. Auto-detected if not provided.
            unhump_sets: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping permission set ARNs to permission set data.
        """
        self.logger.info("Listing SSO permission sets")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        if not instance_arn:
            instance_arn = self.get_sso_instance_arn(execution_role_arn=role_arn)

        sso_admin = self.get_aws_client(
            client_name="sso-admin",
            execution_role_arn=role_arn,
        )

        permission_sets: dict[str, dict[str, Any]] = {}
        paginator = sso_admin.get_paginator("list_permission_sets")

        for page in paginator.paginate(InstanceArn=instance_arn):
            for ps_arn in page.get("PermissionSets", []):
                # Get full details for each permission set
                ps_details = sso_admin.describe_permission_set(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
                )
                permission_sets[ps_arn] = ps_details.get("PermissionSet", {})

        if unhump_sets:
            permission_sets = {k: unhump_map(v) for k, v in permission_sets.items()}

        self.logger.info(f"Retrieved {len(permission_sets)} permission sets")
        return permission_sets

    def get_account_assignments(
        self,
        account_id: str,
        permission_set_arn: str,
        instance_arn: Optional[str] = None,
        unhump_assignments: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get account assignments for a permission set.

        Args:
            account_id: AWS account ID to get assignments for.
            permission_set_arn: Permission set ARN.
            instance_arn: SSO instance ARN. Auto-detected if not provided.
            unhump_assignments: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            List of account assignments.
        """
        self.logger.info(f"Getting account assignments for {account_id}")
        role_arn = execution_role_arn or getattr(self, 'execution_role_arn', None)

        if not instance_arn:
            instance_arn = self.get_sso_instance_arn(execution_role_arn=role_arn)

        sso_admin = self.get_aws_client(
            client_name="sso-admin",
            execution_role_arn=role_arn,
        )

        assignments: list[dict[str, Any]] = []
        paginator = sso_admin.get_paginator("list_account_assignments")

        for page in paginator.paginate(
            InstanceArn=instance_arn,
            AccountId=account_id,
            PermissionSetArn=permission_set_arn
        ):
            for assignment in page.get("AccountAssignments", []):
                assignments.append(assignment)

        if unhump_assignments:
            assignments = [unhump_map(a) for a in assignments]

        self.logger.info(f"Retrieved {len(assignments)} assignments for {account_id}")
        return assignments
