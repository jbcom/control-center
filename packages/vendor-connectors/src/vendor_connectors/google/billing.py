"""Google Cloud Billing operations.

This module provides operations for managing Google Cloud billing accounts
and project billing associations.
"""

from __future__ import annotations

from typing import Any, Optional

from extended_data_types import unhump_map


class GoogleBillingMixin:
    """Mixin providing Google Cloud Billing operations.

    This mixin requires the base GoogleConnector class to provide:
    - get_billing_service()
    - logger
    """

    def list_billing_accounts(
        self,
        filter_query: Optional[str] = None,
        unhump_accounts: bool = False,
    ) -> list[dict[str, Any]]:
        """List Google Cloud billing accounts.

        Args:
            filter_query: Optional filter query string.
            unhump_accounts: Convert keys to snake_case. Defaults to False.

        Returns:
            List of billing account dictionaries.
        """
        self.logger.info("Listing Google Cloud billing accounts")
        service = self.get_billing_service()

        accounts: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {}
            if filter_query:
                params["filter"] = filter_query
            if page_token:
                params["pageToken"] = page_token

            response = service.billingAccounts().list(**params).execute()
            accounts.extend(response.get("billingAccounts", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(accounts)} billing accounts")

        if unhump_accounts:
            accounts = [unhump_map(a) for a in accounts]

        return accounts

    def get_billing_account(self, billing_account_id: str) -> Optional[dict[str, Any]]:
        """Get a specific billing account.

        Args:
            billing_account_id: The billing account ID.

        Returns:
            Billing account dictionary or None if not found.
        """
        from googleapiclient.errors import HttpError

        service = self.get_billing_service()
        name = billing_account_id
        if not name.startswith("billingAccounts/"):
            name = f"billingAccounts/{billing_account_id}"

        try:
            account = service.billingAccounts().get(name=name).execute()
            return account
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"Billing account not found: {billing_account_id}")
                return None
            raise

    def get_project_billing_info(self, project_id: str) -> Optional[dict[str, Any]]:
        """Get billing info for a project.

        Args:
            project_id: The project ID.

        Returns:
            Billing info dictionary or None if not set.
        """
        from googleapiclient.errors import HttpError

        service = self.get_billing_service()

        try:
            billing_info = service.projects().getBillingInfo(name=f"projects/{project_id}").execute()
            return billing_info
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"Project billing info not found: {project_id}")
                return None
            raise

    def update_project_billing_info(
        self,
        project_id: str,
        billing_account_name: str,
    ) -> dict[str, Any]:
        """Link a project to a billing account.

        Args:
            project_id: The project ID.
            billing_account_name: Billing account name (billingAccounts/ACCOUNT_ID).

        Returns:
            Updated billing info dictionary.
        """
        self.logger.info(f"Linking project {project_id} to {billing_account_name}")
        service = self.get_billing_service()

        if not billing_account_name.startswith("billingAccounts/"):
            billing_account_name = f"billingAccounts/{billing_account_name}"

        result = (
            service.projects()
            .updateBillingInfo(
                name=f"projects/{project_id}",
                body={"billingAccountName": billing_account_name},
            )
            .execute()
        )

        self.logger.info(f"Linked project {project_id} to billing account")
        return result

    def disable_project_billing(self, project_id: str) -> dict[str, Any]:
        """Disable billing for a project.

        Args:
            project_id: The project ID.

        Returns:
            Updated billing info dictionary.
        """
        self.logger.info(f"Disabling billing for project {project_id}")
        service = self.get_billing_service()

        result = (
            service.projects()
            .updateBillingInfo(
                name=f"projects/{project_id}",
                body={"billingAccountName": ""},
            )
            .execute()
        )

        self.logger.info(f"Disabled billing for project {project_id}")
        return result

    def list_billing_account_projects(
        self,
        billing_account_id: str,
        unhump_projects: bool = False,
    ) -> list[dict[str, Any]]:
        """List projects linked to a billing account.

        Args:
            billing_account_id: The billing account ID.
            unhump_projects: Convert keys to snake_case. Defaults to False.

        Returns:
            List of project billing info dictionaries.
        """
        self.logger.info(f"Listing projects for billing account {billing_account_id}")
        service = self.get_billing_service()

        name = billing_account_id
        if not name.startswith("billingAccounts/"):
            name = f"billingAccounts/{billing_account_id}"

        projects: list[dict[str, Any]] = []
        page_token = None

        while True:
            params: dict[str, Any] = {"name": name}
            if page_token:
                params["pageToken"] = page_token

            response = service.billingAccounts().projects().list(**params).execute()
            projects.extend(response.get("projectBillingInfo", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        self.logger.info(f"Retrieved {len(projects)} projects")

        if unhump_projects:
            projects = [unhump_map(p) for p in projects]

        return projects

    def get_billing_account_iam_policy(
        self,
        billing_account_id: str,
    ) -> dict[str, Any]:
        """Get IAM policy for a billing account.

        Args:
            billing_account_id: The billing account ID.

        Returns:
            IAM policy dictionary.
        """
        service = self.get_billing_service()

        name = billing_account_id
        if not name.startswith("billingAccounts/"):
            name = f"billingAccounts/{billing_account_id}"

        result = service.billingAccounts().getIamPolicy(resource=name).execute()
        return result

    def set_billing_account_iam_policy(
        self,
        billing_account_id: str,
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Set IAM policy for a billing account.

        Args:
            billing_account_id: The billing account ID.
            policy: IAM policy dictionary.

        Returns:
            Updated IAM policy dictionary.
        """
        self.logger.info(f"Setting IAM policy on billing account {billing_account_id}")
        service = self.get_billing_service()

        name = billing_account_id
        if not name.startswith("billingAccounts/"):
            name = f"billingAccounts/{billing_account_id}"

        result = (
            service.billingAccounts()
            .setIamPolicy(
                resource=name,
                body={"policy": policy},
            )
            .execute()
        )

        return result
