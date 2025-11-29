"""AWS Organizations and Control Tower operations.

This module provides operations for managing AWS accounts through
AWS Organizations and Control Tower.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Optional

from deepmerge import always_merger
from extended_data_types import is_nothing, unhump_map

if TYPE_CHECKING:
    pass


class AWSOrganizationsMixin:
    """Mixin providing AWS Organizations operations.

    This mixin requires the base AWSConnector class to provide:
    - get_aws_client()
    - logger
    - execution_role_arn
    """

    def get_organization_accounts(
        self,
        unhump_accounts: bool = True,
        sort_by_name: bool = False,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all AWS accounts from AWS Organizations.

        Recursively traverses the organization hierarchy to get all accounts
        with their organizational unit information and tags.

        Args:
            unhump_accounts: Convert keys to snake_case. Defaults to True.
            sort_by_name: Sort accounts by name. Defaults to False.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping account IDs to account data including:
            - Name, Email, Status, JoinedTimestamp
            - OuId, OuArn, OuName (organizational unit info)
            - tags (account tags)
            - managed (always False for org accounts)

        Raises:
            RuntimeError: If unable to find root parent ID.
        """
        self.logger.info("Getting AWS organization accounts")

        org_units: dict[str, dict[str, Any]] = {}
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=role_arn,
        )

        self.logger.info("Getting root information")
        roots = orgs.list_roots()

        try:
            root_parent_id = roots["Roots"][0]["Id"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Failed to find root parent ID: {roots}") from exc

        self.logger.info(f"Root parent ID: {root_parent_id}")

        accounts_paginator = orgs.get_paginator("list_accounts_for_parent")
        ou_paginator = orgs.get_paginator("list_organizational_units_for_parent")
        tags_paginator = orgs.get_paginator("list_tags_for_resource")

        def yield_tag_keypairs(tags: list[dict[str, str]]):
            for tag in tags:
                yield tag["Key"], tag["Value"]

        def get_accounts_recursive(parent_id: str) -> dict[str, dict[str, Any]]:
            accounts: dict[str, dict[str, Any]] = {}

            for page in accounts_paginator.paginate(ParentId=parent_id):
                for account in page["Accounts"]:
                    account_id = account["Id"]
                    account_tags: dict[str, str] = {}
                    for tags_page in tags_paginator.paginate(ResourceId=account_id):
                        for k, v in yield_tag_keypairs(tags_page["Tags"]):
                            account_tags[k] = v

                    account["tags"] = account_tags
                    accounts[account_id] = account

            for page in ou_paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    ou_id = ou["Id"]
                    ou_data = org_units.get(ou_id)
                    if is_nothing(ou_data):
                        ou_data = {}
                        for k, v in deepcopy(ou).items():
                            ou_data[f"Ou{k.title()}"] = v
                        org_units[ou_id] = ou_data

                    for account_id, account_data in get_accounts_recursive(ou_id).items():
                        accounts[account_id] = always_merger.merge(deepcopy(account_data), deepcopy(ou_data))

            return accounts

        aws_accounts = get_accounts_recursive(root_parent_id)

        # Mark all as unmanaged initially
        for account_id in list(aws_accounts.keys()):
            aws_accounts[account_id]["managed"] = False

        # Apply transformations
        if unhump_accounts:
            aws_accounts = {k: unhump_map(v) for k, v in aws_accounts.items()}

        if sort_by_name:
            key_field = "name" if unhump_accounts else "Name"
            aws_accounts = dict(sorted(aws_accounts.items(), key=lambda x: x[1].get(key_field, "")))

        self.logger.info(f"Retrieved {len(aws_accounts)} organization accounts")
        return aws_accounts

    def get_controltower_accounts(
        self,
        unhump_accounts: bool = True,
        sort_by_name: bool = False,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all AWS accounts managed by AWS Control Tower.

        Retrieves accounts from the Control Tower Account Factory.

        Args:
            unhump_accounts: Convert keys to snake_case. Defaults to True.
            sort_by_name: Sort accounts by name. Defaults to False.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping account IDs to account data with managed=True.
        """
        from botocore.exceptions import ClientError

        self.logger.info("Getting AWS Control Tower accounts")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        servicecatalog = self.get_aws_client(
            client_name="servicecatalog",
            execution_role_arn=role_arn,
        )

        accounts: dict[str, dict[str, Any]] = {}

        try:
            sc_paginator = servicecatalog.get_paginator("search_provisioned_products")
            for page in sc_paginator.paginate(Filters={"SearchQuery": ["productType:CONTROL_TOWER_ACCOUNT"]}):
                for product in page.get("ProvisionedProducts", []):
                    account_data = {
                        "Name": product.get("Name", ""),
                        "Status": product.get("Status", ""),
                        "managed": True,
                        "ProvisionedProductId": product.get("Id"),
                    }

                    if product.get("Id"):
                        try:
                            outputs = servicecatalog.get_provisioned_product_outputs(ProvisionedProductId=product["Id"])
                            for output in outputs.get("Outputs", []):
                                if output.get("OutputKey") == "AccountId":
                                    account_id = output.get("OutputValue")
                                    if account_id:
                                        accounts[account_id] = account_data
                                        break
                        except ClientError:
                            pass

        except ClientError as e:
            self.logger.warning(f"Could not list Control Tower accounts: {e}")

        # Apply transformations
        if unhump_accounts:
            accounts = {k: unhump_map(v) for k, v in accounts.items()}

        if sort_by_name:
            key_field = "name" if unhump_accounts else "Name"
            accounts = dict(sorted(accounts.items(), key=lambda x: x[1].get(key_field, "")))

        self.logger.info(f"Retrieved {len(accounts)} Control Tower accounts")
        return accounts

    def get_accounts(
        self,
        unhump_accounts: bool = True,
        sort_by_name: bool = False,
        include_controltower: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all AWS accounts from Organizations and Control Tower.

        Combines accounts from AWS Organizations and Control Tower, marking
        Control Tower accounts as 'managed'.

        Args:
            unhump_accounts: Convert keys to snake_case. Defaults to True.
            sort_by_name: Sort accounts by name. Defaults to False.
            include_controltower: Include Control Tower accounts. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping account IDs to account data with 'managed' flag.
        """
        self.logger.info("Getting all AWS accounts")

        # Get organization accounts
        aws_accounts = self.get_organization_accounts(
            unhump_accounts=False,
            sort_by_name=False,
            execution_role_arn=execution_role_arn,
        )

        # Merge with Control Tower accounts
        if include_controltower:
            controltower_accounts = self.get_controltower_accounts(
                unhump_accounts=False,
                sort_by_name=False,
                execution_role_arn=execution_role_arn,
            )
            aws_accounts = always_merger.merge(aws_accounts, controltower_accounts)

        # Apply transformations
        if unhump_accounts:
            aws_accounts = {k: unhump_map(v) for k, v in aws_accounts.items()}

        if sort_by_name:
            key_field = "name" if unhump_accounts else "Name"
            aws_accounts = dict(sorted(aws_accounts.items(), key=lambda x: x[1].get(key_field, "")))

        self.logger.info(f"Retrieved {len(aws_accounts)} total AWS accounts")
        return aws_accounts

    def get_organization_units(
        self,
        unhump_units: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all organizational units from AWS Organizations.

        Args:
            unhump_units: Convert keys to snake_case. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary mapping OU IDs to OU data.
        """
        self.logger.info("Getting AWS organizational units")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=role_arn,
        )

        roots = orgs.list_roots()
        root_parent_id = roots["Roots"][0]["Id"]

        ou_paginator = orgs.get_paginator("list_organizational_units_for_parent")
        org_units: dict[str, dict[str, Any]] = {}

        def get_ous_recursive(parent_id: str, parent_path: str = ""):
            for page in ou_paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    ou_id = ou["Id"]
                    ou_path = f"{parent_path}/{ou['Name']}" if parent_path else ou["Name"]
                    ou["Path"] = ou_path
                    org_units[ou_id] = ou
                    get_ous_recursive(ou_id, ou_path)

        get_ous_recursive(root_parent_id)

        if unhump_units:
            org_units = {k: unhump_map(v) for k, v in org_units.items()}

        self.logger.info(f"Retrieved {len(org_units)} organizational units")
        return org_units
