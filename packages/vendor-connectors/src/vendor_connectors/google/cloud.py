"""Google Cloud Platform resource management operations.

This module provides operations for managing Google Cloud organizations,
folders, projects, and IAM.
"""

from __future__ import annotations

from typing import Any, Optional

from extended_data_types import unhump_map


class GoogleCloudMixin:
    """Mixin providing Google Cloud Platform operations.

    This mixin requires the base GoogleConnector class to provide:
    - get_cloud_resource_manager_service()
    - get_iam_service()
    - logger
    """

    def get_organization_id(self) -> str:
        """Get the Google Cloud organization ID.

        Returns:
            The organization ID (numeric string).

        Raises:
            RuntimeError: If no organization is found.
        """
        self.logger.info("Getting Google Cloud organization ID")
        service = self.get_cloud_resource_manager_service()

        response = service.organizations().search().execute()
        organizations = response.get("organizations", [])

        if not organizations:
            raise RuntimeError("No organizations found")

        org_name = organizations[0]["name"]
        org_id = org_name.split("/")[-1]
        self.logger.info(f"Organization ID: {org_id}")
        return org_id

    def get_organization(self) -> dict[str, Any]:
        """Get the Google Cloud organization details.

        Returns:
            Organization dictionary.

        Raises:
            RuntimeError: If no organization is found.
        """
        self.logger.info("Getting Google Cloud organization")
        service = self.get_cloud_resource_manager_service()

        response = service.organizations().search().execute()
        organizations = response.get("organizations", [])

        if not organizations:
            raise RuntimeError("No organizations found")

        return organizations[0]

    def list_projects(
        self,
        parent: Optional[str] = None,
        filter_query: Optional[str] = None,
        unhump_projects: bool = False,
    ) -> list[dict[str, Any]]:
        """List Google Cloud projects.

        Args:
            parent: Parent resource (organizations/ORG_ID or folders/FOLDER_ID).
            filter_query: Optional filter query string.
            unhump_projects: Convert keys to snake_case. Defaults to False.

        Returns:
            List of project dictionaries.
        """
        self.logger.info("Listing Google Cloud projects")
        service = self.get_cloud_resource_manager_service()

        projects: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {}
            if parent:
                params["parent"] = parent
            if filter_query:
                params["filter"] = filter_query
            if page_token:
                params["pageToken"] = page_token

            response = service.projects().search(**params).execute()
            projects.extend(response.get("projects", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(projects)} projects")

        if unhump_projects:
            projects = [unhump_map(p) for p in projects]

        return projects

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """Get a specific Google Cloud project.

        Args:
            project_id: The project ID.

        Returns:
            Project dictionary or None if not found.
        """
        from googleapiclient.errors import HttpError

        service = self.get_cloud_resource_manager_service()

        try:
            project = service.projects().get(name=f"projects/{project_id}").execute()
            return project
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"Project not found: {project_id}")
                return None
            raise

    def create_project(
        self,
        project_id: str,
        display_name: str,
        parent: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create a Google Cloud project.

        Args:
            project_id: Unique project ID.
            display_name: Human-readable project name.
            parent: Parent resource (organizations/ORG_ID or folders/FOLDER_ID).
            labels: Optional project labels.

        Returns:
            Operation response dictionary.
        """
        self.logger.info(f"Creating project: {project_id}")
        service = self.get_cloud_resource_manager_service()

        project_body: dict[str, Any] = {
            "projectId": project_id,
            "displayName": display_name,
        }

        if parent:
            project_body["parent"] = parent
        if labels:
            project_body["labels"] = labels

        result = service.projects().create(body=project_body).execute()
        self.logger.info(f"Created project: {project_id}")
        return result

    def delete_project(self, project_id: str) -> dict[str, Any]:
        """Delete a Google Cloud project.

        Args:
            project_id: The project ID to delete.

        Returns:
            Operation response dictionary.
        """
        self.logger.info(f"Deleting project: {project_id}")
        service = self.get_cloud_resource_manager_service()

        result = service.projects().delete(name=f"projects/{project_id}").execute()
        self.logger.info(f"Deleted project: {project_id}")
        return result

    def move_project(
        self,
        project_id: str,
        destination_parent: str,
    ) -> dict[str, Any]:
        """Move a project to a different folder/organization.

        Args:
            project_id: The project ID to move.
            destination_parent: Destination (organizations/ORG_ID or folders/FOLDER_ID).

        Returns:
            Operation response dictionary.
        """
        self.logger.info(f"Moving project {project_id} to {destination_parent}")
        service = self.get_cloud_resource_manager_service()

        result = (
            service.projects()
            .move(
                name=f"projects/{project_id}",
                body={"destinationParent": destination_parent},
            )
            .execute()
        )
        self.logger.info(f"Moved project {project_id}")
        return result

    def list_folders(
        self,
        parent: str,
        unhump_folders: bool = False,
    ) -> list[dict[str, Any]]:
        """List folders under a parent.

        Args:
            parent: Parent resource (organizations/ORG_ID or folders/FOLDER_ID).
            unhump_folders: Convert keys to snake_case. Defaults to False.

        Returns:
            List of folder dictionaries.
        """
        self.logger.info(f"Listing folders under {parent}")
        service = self.get_cloud_resource_manager_service()

        folders: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"parent": parent}
            if page_token:
                params["pageToken"] = page_token

            response = service.folders().list(**params).execute()
            folders.extend(response.get("folders", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(folders)} folders")

        if unhump_folders:
            folders = [unhump_map(f) for f in folders]

        return folders

    def get_org_policy(
        self,
        resource: str,
        constraint: str,
    ) -> Optional[dict[str, Any]]:
        """Get an organization policy.

        Args:
            resource: Resource name (organizations/ORG_ID, folders/FOLDER_ID, projects/PROJECT_ID).
            constraint: Policy constraint name.

        Returns:
            Policy dictionary or None if not set.
        """
        from googleapiclient.errors import HttpError

        service = self.get_cloud_resource_manager_service()

        try:
            policy = (
                service.organizations()
                .getOrgPolicy(
                    resource=resource,
                    body={"constraint": constraint},
                )
                .execute()
            )
            return policy
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise

    def set_org_policy(
        self,
        resource: str,
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Set an organization policy.

        Args:
            resource: Resource name (organizations/ORG_ID, folders/FOLDER_ID, projects/PROJECT_ID).
            policy: Policy dictionary.

        Returns:
            Updated policy dictionary.
        """
        self.logger.info(f"Setting org policy on {resource}")
        service = self.get_cloud_resource_manager_service()

        result = (
            service.organizations()
            .setOrgPolicy(
                resource=resource,
                body={"policy": policy},
            )
            .execute()
        )
        return result

    def get_iam_policy(
        self,
        resource: str,
        resource_type: str = "projects",
    ) -> dict[str, Any]:
        """Get IAM policy for a resource.

        Args:
            resource: Resource ID.
            resource_type: Type of resource (projects, folders, organizations).

        Returns:
            IAM policy dictionary.
        """
        service = self.get_cloud_resource_manager_service()

        if resource_type == "projects":
            result = (
                service.projects()
                .getIamPolicy(
                    resource=f"projects/{resource}",
                    body={},
                )
                .execute()
            )
        elif resource_type == "folders":
            result = (
                service.folders()
                .getIamPolicy(
                    resource=f"folders/{resource}",
                    body={},
                )
                .execute()
            )
        else:  # organizations
            result = (
                service.organizations()
                .getIamPolicy(
                    resource=f"organizations/{resource}",
                    body={},
                )
                .execute()
            )

        return result

    def set_iam_policy(
        self,
        resource: str,
        policy: dict[str, Any],
        resource_type: str = "projects",
    ) -> dict[str, Any]:
        """Set IAM policy for a resource.

        Args:
            resource: Resource ID.
            policy: IAM policy dictionary.
            resource_type: Type of resource (projects, folders, organizations).

        Returns:
            Updated IAM policy dictionary.
        """
        self.logger.info(f"Setting IAM policy on {resource_type}/{resource}")
        service = self.get_cloud_resource_manager_service()

        body = {"policy": policy}

        if resource_type == "projects":
            result = (
                service.projects()
                .setIamPolicy(
                    resource=f"projects/{resource}",
                    body=body,
                )
                .execute()
            )
        elif resource_type == "folders":
            result = (
                service.folders()
                .setIamPolicy(
                    resource=f"folders/{resource}",
                    body=body,
                )
                .execute()
            )
        else:  # organizations
            result = (
                service.organizations()
                .setIamPolicy(
                    resource=f"organizations/{resource}",
                    body=body,
                )
                .execute()
            )

        self.logger.info(f"Set IAM policy on {resource_type}/{resource}")
        return result

    def add_iam_binding(
        self,
        resource: str,
        role: str,
        member: str,
        resource_type: str = "projects",
    ) -> dict[str, Any]:
        """Add an IAM binding to a resource.

        Args:
            resource: Resource ID.
            role: IAM role to grant.
            member: Member to grant role to (user:, group:, serviceAccount:).
            resource_type: Type of resource (projects, folders, organizations).

        Returns:
            Updated IAM policy dictionary.
        """
        self.logger.info(f"Adding IAM binding: {role} -> {member} on {resource}")

        policy = self.get_iam_policy(resource, resource_type)
        bindings = policy.get("bindings", [])

        # Find existing binding for role
        role_binding = None
        for binding in bindings:
            if binding.get("role") == role:
                role_binding = binding
                break

        if role_binding:
            if member not in role_binding.get("members", []):
                role_binding["members"].append(member)
        else:
            bindings.append({"role": role, "members": [member]})

        policy["bindings"] = bindings
        return self.set_iam_policy(resource, policy, resource_type)

    def list_service_accounts(
        self,
        project_id: str,
        unhump_accounts: bool = False,
    ) -> list[dict[str, Any]]:
        """List service accounts in a project.

        Args:
            project_id: The project ID.
            unhump_accounts: Convert keys to snake_case. Defaults to False.

        Returns:
            List of service account dictionaries.
        """
        self.logger.info(f"Listing service accounts in {project_id}")
        service = self.get_iam_service()

        accounts: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"name": f"projects/{project_id}"}
            if page_token:
                params["pageToken"] = page_token

            response = service.projects().serviceAccounts().list(**params).execute()
            accounts.extend(response.get("accounts", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(accounts)} service accounts")

        if unhump_accounts:
            accounts = [unhump_map(a) for a in accounts]

        return accounts

    def create_service_account(
        self,
        project_id: str,
        account_id: str,
        display_name: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a service account in a project.

        Args:
            project_id: The project ID.
            account_id: Unique account ID (alphanumeric, 6-30 chars).
            display_name: Human-readable name.
            description: Optional description.

        Returns:
            Created service account dictionary.
        """
        self.logger.info(f"Creating service account: {account_id} in {project_id}")
        service = self.get_iam_service()

        result = (
            service.projects()
            .serviceAccounts()
            .create(
                name=f"projects/{project_id}",
                body={
                    "accountId": account_id,
                    "serviceAccount": {
                        "displayName": display_name,
                        "description": description,
                    },
                },
            )
            .execute()
        )

        self.logger.info(f"Created service account: {result.get('email')}")
        return result
