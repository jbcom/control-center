"""AWS Organizations and Control Tower operations.

This module provides operations for managing AWS accounts through
AWS Organizations and Control Tower.
"""

from __future__ import annotations

import re
from collections import defaultdict
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

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _build_org_units_with_tags(
        self,
        role_arn: Optional[str],
    ) -> dict[str, dict[str, Any]]:
        """Fetch organizational units including tag metadata."""

        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=role_arn,
        )
        tags_paginator = orgs.get_paginator("list_tags_for_resource")
        ou_paginator = orgs.get_paginator("list_organizational_units_for_parent")
        roots = orgs.list_roots()
        root_parent_id = roots["Roots"][0]["Id"]

        units: dict[str, dict[str, Any]] = {}

        def get_tags(resource_id: str) -> dict[str, str]:
            tag_map: dict[str, str] = {}
            for page in tags_paginator.paginate(ResourceId=resource_id):
                for tag in page.get("Tags", []):
                    tag_map[tag["Key"]] = tag["Value"]
            return tag_map

        def walk(parent_id: str):
            for page in ou_paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    ou_id = ou["Id"]
                    unit_entry = {
                        "id": ou_id,
                        "name": ou["Name"],
                        "arn": ou.get("Arn"),
                        "tags": get_tags(ou_id),
                        "control_tower_organizational_unit": f"{ou['Name']} ({ou_id})",
                    }
                    units[ou_id] = unit_entry
                    walk(ou_id)

        walk(root_parent_id)
        return units

    def _build_labeled_account(
        self,
        account_id: str,
        account_data: dict[str, Any],
        controltower_data: Optional[dict[str, Any]],
        units_lookup: dict[str, dict[str, Any]],
        domains: dict[str, str],
        caller_account_id: str,
    ) -> dict[str, Any]:
        """Normalize metadata for a single AWS account."""

        tags = account_data.get("tags", {})
        managed = bool(account_data.get("managed") or (controltower_data and controltower_data.get("managed")))
        account_name = account_data.get("Name") or account_data.get("name") or account_id
        email = account_data.get("Email") or account_data.get("email")
        parent_id = account_data.get("OuId") or account_data.get("ou_id")
        organizational_unit = account_data.get("OuName") or account_data.get("ou_name")

        if controltower_data:
            tags = {**controltower_data.get("tags", {}), **tags}
            organizational_unit = controltower_data.get("OrganizationalUnit") or organizational_unit
            parent_id = controltower_data.get("parent_id") or parent_id

        unit_metadata = {}
        if parent_id and parent_id in units_lookup:
            unit_metadata = deepcopy(units_lookup[parent_id])
        elif organizational_unit:
            normalized = organizational_unit.lower()
            for unit in units_lookup.values():
                if (unit.get("name") or "").lower() == normalized:
                    unit_metadata = deepcopy(unit)
                    break

        def _slug(value: str) -> str:
            sanitized = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
            return sanitized or re.sub(r"[^A-Za-z0-9]+", "", account_id)

        normalized_name = account_name.replace(" ", "")
        json_key = _slug(normalized_name.replace("-", "_"))
        network_name = normalized_name.replace("_", "-").lower()

        root_account = account_id == caller_account_id
        execution_role_name = "" if root_account else tags.get("ExecutionRoleName", "AWSControlTowerExecution")
        execution_role_arn = ""
        if execution_role_name and not root_account:
            execution_role_arn = f"arn:aws:iam::{account_id}:role/{execution_role_name}"

        env_default = "dev" if account_name.startswith("User-") else "global"
        environment = tags.get("Environment") or unit_metadata.get("tags", {}).get("Environment") or env_default

        domain = account_data.get("domain") or domains.get(environment) or domains.get("default")
        subdomain = domain
        if environment in {"stg", "prod"} and domain and not domain.startswith(network_name):
            subdomain = f"{network_name}.{domain}"

        def _process_classifications(value: str) -> list[str]:
            if not value:
                return []
            return [
                re.sub(r"[^A-Za-z0-9_-]+", "_", item).lower().removesuffix("_accounts")
                for item in value.split()
                if item
            ]

        unit_tags = unit_metadata.get("tags", {})
        classifications = list(
            set(
                _process_classifications(tags.get("Classifications", ""))
                + _process_classifications(unit_tags.get("Classifications", ""))
            )
        )

        spoke = bool(tags.get("Spoke") or unit_tags.get("Spoke") or tags.get("spoke") or unit_tags.get("spoke"))

        labeled = {
            "id": account_id,
            "account_id": account_id,
            "account_name": account_name,
            "name": account_name,
            "email": email,
            "managed": managed,
            "tags": tags,
            "json_key": json_key,
            "network_name": network_name,
            "organizational_unit": organizational_unit,
            "unit": unit_metadata.get("name"),
            "unit_metadata": unit_metadata,
            "execution_role_arn": execution_role_arn,
            "environment": environment,
            "domain": domain,
            "subdomain": subdomain,
            "spoke": spoke,
            "classifications": classifications or ["accounts"],
        }

        if controltower_data:
            labeled["provisioned_product_id"] = controltower_data.get("ProvisionedProductId")

        return labeled

    def label_account(
        self,
        account_id: str,
        labels: dict[str, str],
        execution_role_arn: Optional[str] = None,
    ) -> None:
        """Apply labels (tags) to an AWS account.

        Args:
            account_id: AWS account ID.
            labels: Dictionary of label key-value pairs to apply.
            execution_role_arn: ARN of role to assume for cross-account access.
        """
        self.logger.info(f"Labeling AWS account {account_id} with {len(labels)} tags")
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)

        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=role_arn,
        )

        tags = [{"Key": k, "Value": v} for k, v in labels.items()]
        orgs.tag_resource(ResourceId=account_id, Tags=tags)
        self.logger.info(f"Applied {len(labels)} tags to account {account_id}")

    def classify_accounts(
        self,
        accounts: Optional[dict[str, dict[str, Any]]] = None,
        classification_rules: Optional[dict[str, list[str]]] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Classify AWS accounts based on OU paths or tags.

        Default classification rules:
        - 'production': accounts in OUs containing 'prod' or 'production'
        - 'staging': accounts in OUs containing 'stage' or 'staging'
        - 'development': accounts in OUs containing 'dev' or 'development'
        - 'sandbox': accounts in OUs containing 'sandbox'
        - 'security': accounts in OUs containing 'security'

        Args:
            accounts: Pre-fetched accounts dict. Fetched if not provided.
            classification_rules: Custom rules mapping classification -> OU patterns.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Accounts dict with added 'classification' field.
        """
        self.logger.info("Classifying AWS accounts")

        if accounts is None:
            accounts = self.get_accounts(
                unhump_accounts=True,
                execution_role_arn=execution_role_arn,
            )

        default_rules = {
            "production": ["prod", "production"],
            "staging": ["stage", "staging"],
            "development": ["dev", "development"],
            "sandbox": ["sandbox"],
            "security": ["security"],
            "shared": ["shared", "common"],
            "workloads": ["workloads", "workload"],
        }
        rules = classification_rules or default_rules

        for account_id, account_data in accounts.items():
            ou_name = account_data.get("ou_name", "").lower()
            ou_path = account_data.get("path", "").lower() if "path" in account_data else ""
            tags = account_data.get("tags", {})

            classification = "unclassified"
            for class_name, patterns in rules.items():
                for pattern in patterns:
                    if pattern in ou_name or pattern in ou_path:
                        classification = class_name
                        break
                    # Also check tags
                    env_tag = tags.get("Environment", "").lower()
                    if pattern in env_tag:
                        classification = class_name
                        break
                if classification != "unclassified":
                    break

            accounts[account_id]["classification"] = classification

        self.logger.info(f"Classified {len(accounts)} accounts")
        return accounts

    # --------------------------------------------------------------------- #
    # Terraform-migrated helpers                                           #
    # --------------------------------------------------------------------- #

    def label_aws_accounts(
        self,
        domains: dict[str, str],
        aws_organization_units: Optional[dict[str, dict[str, Any]]] = None,
        caller_account_id: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, dict[str, Any]]:
        """Return normalized metadata for every AWS account.

        This mirrors the legacy ``label_aws_account`` helper from terraform-modules.

        Args:
            domains: Mapping of environment -> root domain.
            aws_organization_units: Optional precomputed OU metadata (with tags).
            caller_account_id: Optional root account id. Auto-discovered if omitted.
            execution_role_arn: ARN used for cross-account access.

        Returns:
            Dictionary keyed by account id with normalized metadata (network_name,
            json_key, execution role ARN, classifications, etc.).
        """

        if not domains:
            raise ValueError("domains mapping is required to label AWS accounts")

        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)
        units_lookup = aws_organization_units or self._build_org_units_with_tags(role_arn=role_arn)
        caller_account_id = caller_account_id or self.get_caller_account_id()

        organization_accounts = self.get_organization_accounts(
            unhump_accounts=False,
            sort_by_name=False,
            execution_role_arn=role_arn,
        )
        controltower_accounts = self.get_controltower_accounts(
            unhump_accounts=False,
            sort_by_name=False,
            execution_role_arn=role_arn,
        )

        labeled_accounts: dict[str, dict[str, Any]] = {}

        for account_id, account_data in organization_accounts.items():
            controltower_data = controltower_accounts.get(account_id)
            labeled_accounts[account_id] = self._build_labeled_account(
                account_id=account_id,
                account_data=account_data,
                controltower_data=controltower_data,
                units_lookup=units_lookup,
                domains=domains,
                caller_account_id=caller_account_id,
            )

        # Include Control Tower-only accounts
        for account_id, controltower_data in controltower_accounts.items():
            if account_id in labeled_accounts:
                continue
            labeled_accounts[account_id] = self._build_labeled_account(
                account_id=account_id,
                account_data=controltower_data,
                controltower_data=controltower_data,
                units_lookup=units_lookup,
                domains=domains,
                caller_account_id=caller_account_id,
            )

        return labeled_accounts

    def label_aws_account(
        self,
        account_id: str,
        domains: dict[str, str],
        aws_organization_units: Optional[dict[str, dict[str, Any]]] = None,
        caller_account_id: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return metadata for a single AWS account."""

        labeled_accounts = self.label_aws_accounts(
            domains=domains,
            aws_organization_units=aws_organization_units,
            caller_account_id=caller_account_id,
            execution_role_arn=execution_role_arn,
        )
        try:
            return labeled_accounts[account_id]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise KeyError(f"AWS account {account_id} not found") from exc

    def classify_aws_accounts(
        self,
        labeled_accounts: Optional[dict[str, dict[str, Any]]] = None,
        suffix: Optional[str] = None,
        domains: Optional[dict[str, str]] = None,
        aws_organization_units: Optional[dict[str, dict[str, Any]]] = None,
        caller_account_id: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, list[str]]:
        """Group accounts by classification, matching terraform-modules output."""

        if labeled_accounts is None:
            if not domains:
                raise ValueError("domains mapping required when labeled_accounts is not provided")
            labeled_accounts = self.label_aws_accounts(
                domains=domains,
                aws_organization_units=aws_organization_units,
                caller_account_id=caller_account_id,
                execution_role_arn=execution_role_arn,
            )

        suffix_value = f"_accounts{suffix}" if suffix else "_accounts"
        classified_accounts: dict[str, list[str]] = defaultdict(list)

        for account_key, account_data in labeled_accounts.items():
            for classification in account_data.get("classifications", []):
                if not classification or classification == "accounts":
                    continue
                classified_accounts[f"{classification}{suffix_value}"].append(account_key)

        return dict(classified_accounts)

    def preprocess_aws_organization(
        self,
        domains: dict[str, str],
        suffix: Optional[str] = None,
        aws_organization_units: Optional[dict[str, dict[str, Any]]] = None,
        caller_account_id: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build full organization context (accounts, units, lookups)."""

        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)
        units_lookup = aws_organization_units or self._build_org_units_with_tags(role_arn=role_arn)

        labeled_accounts = self.label_aws_accounts(
            domains=domains,
            aws_organization_units=units_lookup,
            caller_account_id=caller_account_id,
            execution_role_arn=role_arn,
        )
        classification_lookup = self.classify_aws_accounts(
            labeled_accounts=labeled_accounts,
            suffix=suffix,
        )

        accounts_by_name = {
            data["account_name"]: data for data in labeled_accounts.values() if data.get("account_name")
        }
        accounts_by_email = {data["email"]: data for data in labeled_accounts.values() if data.get("email")}
        accounts_by_key = {data["json_key"]: data for data in labeled_accounts.values() if data.get("json_key")}

        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=role_arn,
        )
        root_id = orgs.list_roots()["Roots"][0]["Id"]

        units_by_name = {unit["name"]: unit for unit in units_lookup.values() if unit.get("name")}

        result = {
            "accounts": labeled_accounts,
            "units": units_lookup,
            "unit_classifications_by_name": {
                name: unit.get("classifications", []) for name, unit in units_by_name.items()
            },
            "accounts_by_classification": classification_lookup,
            "accounts_by_name": accounts_by_name,
            "accounts_by_email": accounts_by_email,
            "accounts_by_key": accounts_by_key,
            "organization": {
                "root_id": root_id,
                "organizational_units": units_lookup,
                "account_count": len(labeled_accounts),
                "ou_count": len(units_lookup),
            },
        }

        return result

    def preprocess_organization(
        self,
        include_tags: bool = True,
        include_classification: bool = True,
        execution_role_arn: Optional[str] = None,
    ) -> dict[str, Any]:
        """Preprocess AWS Organization data for terraform consumption.

        Returns a structured dict suitable for terraform data sources.

        Args:
            include_tags: Include account tags. Defaults to True.
            include_classification: Include account classification. Defaults to True.
            execution_role_arn: ARN of role to assume for cross-account access.

        Returns:
            Dictionary with 'accounts', 'organizational_units', and 'root_id'.
        """
        self.logger.info("Preprocessing AWS Organization data")

        accounts = self.get_accounts(
            unhump_accounts=True,
            include_controltower=True,
            execution_role_arn=execution_role_arn,
        )

        if include_classification:
            accounts = self.classify_accounts(
                accounts=accounts,
                execution_role_arn=execution_role_arn,
            )

        org_units = self.get_organization_units(
            unhump_units=True,
            execution_role_arn=execution_role_arn,
        )

        # Get root ID
        role_arn = execution_role_arn or getattr(self, "execution_role_arn", None)
        orgs = self.get_aws_client(
            client_name="organizations",
            execution_role_arn=role_arn,
        )
        roots = orgs.list_roots()
        root_id = roots["Roots"][0]["Id"]

        result = {
            "root_id": root_id,
            "accounts": accounts,
            "organizational_units": org_units,
            "account_count": len(accounts),
            "ou_count": len(org_units),
        }

        self.logger.info(f"Preprocessed org: {len(accounts)} accounts, {len(org_units)} OUs")
        return result
