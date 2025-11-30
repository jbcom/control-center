"""Tests for AWS Organizations helper mixin."""

from __future__ import annotations

from typing import Any

import pytest

from vendor_connectors.aws.organizations import AWSOrganizationsMixin


class _StubLogger:
    def info(self, *args, **kwargs):  # pragma: no cover - no logic to test
        pass

    def debug(self, *args, **kwargs):  # pragma: no cover - no logic to test
        pass

    def warning(self, *args, **kwargs):  # pragma: no cover - no logic to test
        pass


class _StubOrganizationsClient:
    def __init__(self) -> None:
        self.tag_calls: list[dict[str, Any]] = []

    def tag_resource(self, ResourceId: str, Tags: list[dict[str, str]]):
        self.tag_calls.append({"ResourceId": ResourceId, "Tags": Tags})

    def list_roots(self):
        return {"Roots": [{"Id": "r-root"}]}


class _TestAWSOrganizations(AWSOrganizationsMixin):
    def __init__(self) -> None:
        self.logger = _StubLogger()
        self.execution_role_arn = "arn:aws:iam::111111111111:role/test"
        self._clients: dict[str, Any] = {}

    def register_client(self, name: str, client: Any) -> None:
        self._clients[name] = client

    def get_aws_client(self, client_name: str, execution_role_arn=None):
        return self._clients[client_name]


@pytest.fixture()
def organizations_connector() -> _TestAWSOrganizations:
    connector = _TestAWSOrganizations()
    connector.register_client("organizations", _StubOrganizationsClient())
    return connector


def test_classify_accounts_applies_rules(organizations_connector: _TestAWSOrganizations):
    accounts = {
        "111111111111": {"ou_name": "Prod Apps", "tags": {}},
        "222222222222": {"path": "Shared/Dev", "tags": {}},
        "333333333333": {"ou_name": "Misc", "tags": {"Environment": "Sandbox"}},
    }

    result = organizations_connector.classify_accounts(
        accounts=accounts,
        classification_rules={
            "production": ["prod"],
            "development": ["dev"],
            "sandbox": ["sandbox"],
        },
    )

    assert result["111111111111"]["classification"] == "production"
    assert result["222222222222"]["classification"] == "development"
    assert result["333333333333"]["classification"] == "sandbox"


def test_classify_accounts_fetches_when_missing(mocker, organizations_connector: _TestAWSOrganizations):
    sample_accounts = {"999999999999": {"ou_name": "Shared", "tags": {"Environment": "Shared"}}}
    mock_get = mocker.patch.object(organizations_connector, "get_accounts", return_value=sample_accounts)

    output = organizations_connector.classify_accounts()

    mock_get.assert_called_once()
    assert output["999999999999"]["classification"] == "shared"


def test_label_account_tags_resource(organizations_connector: _TestAWSOrganizations):
    client = organizations_connector._clients["organizations"]

    organizations_connector.label_account("123456789012", {"Env": "prod", "Owner": "platform"})

    assert client.tag_calls == [
        {
            "ResourceId": "123456789012",
            "Tags": [
                {"Key": "Env", "Value": "prod"},
                {"Key": "Owner", "Value": "platform"},
            ],
        }
    ]


def test_preprocess_organization_compiles_sections(mocker, organizations_connector: _TestAWSOrganizations):
    mock_get_accounts = mocker.patch.object(
        organizations_connector,
        "get_accounts",
        return_value={"123": {"name": "core"}},
    )
    mock_classify = mocker.patch.object(
        organizations_connector,
        "classify_accounts",
        side_effect=lambda accounts, **_: {k: {**v, "classification": "production"} for k, v in accounts.items()},
    )
    mock_get_units = mocker.patch.object(
        organizations_connector,
        "get_organization_units",
        return_value={"ou-1": {"name": "Shared"}},
    )

    result = organizations_connector.preprocess_organization()

    mock_get_accounts.assert_called_once()
    mock_classify.assert_called_once()
    mock_get_units.assert_called_once()

    assert result["root_id"] == "r-root"
    assert result["account_count"] == 1
    assert result["ou_count"] == 1
    assert result["accounts"]["123"]["classification"] == "production"
    assert result["organizational_units"] == {"ou-1": {"name": "Shared"}}


def test_get_accounts_merges_controltower_data(mocker, organizations_connector: _TestAWSOrganizations):
    mock_org = mocker.patch.object(
        organizations_connector,
        "get_organization_accounts",
        return_value={
            "200": {"Name": "Beta", "managed": False},
            "300": {"Name": "Gamma", "managed": False},
        },
    )
    mock_ctrl = mocker.patch.object(
        organizations_connector,
        "get_controltower_accounts",
        return_value={
            "100": {"Name": "Alpha", "managed": True},
            "200": {"Name": "Beta", "managed": True},
        },
    )

    result = organizations_connector.get_accounts(unhump_accounts=True, sort_by_name=True)

    mock_org.assert_called_once()
    mock_ctrl.assert_called_once()

    assert list(result.keys()) == ["100", "200", "300"]
    assert result["200"]["managed"] is True
    assert result["100"]["name"] == "Alpha"


def test_label_aws_accounts_builds_metadata(mocker, organizations_connector: _TestAWSOrganizations):
    mocker.patch.object(
        organizations_connector,
        "get_organization_accounts",
        return_value={
            "123456789012": {
                "Name": "Prod Account",
                "Email": "ops@example.com",
                "OuId": "ou-prod",
                "OuName": "Prod",
                "tags": {"Environment": "prod", "ExecutionRoleName": "CustomRole"},
            }
        },
    )
    mocker.patch.object(organizations_connector, "get_controltower_accounts", return_value={})
    mocker.patch.object(
        organizations_connector,
        "_build_org_units_with_tags",
        return_value={
            "ou-prod": {
                "id": "ou-prod",
                "name": "Prod",
                "tags": {"Spoke": "true"},
            }
        },
    )
    organizations_connector.get_caller_account_id = lambda: "000000000000"  # type: ignore[assignment]

    labeled = organizations_connector.label_aws_accounts(domains={"prod": "example.com"})
    account = labeled["123456789012"]

    assert account["json_key"] == "ProdAccount"
    assert account["execution_role_arn"].endswith("role/CustomRole")
    assert account["environment"] == "prod"
    assert account["spoke"] is True
    assert ".example.com" in account["subdomain"]


def test_classify_aws_accounts_generates_suffix(organizations_connector: _TestAWSOrganizations):
    labeled = {
        "123": {"classifications": ["production", "shared"]},
        "456": {"classifications": ["development"]},
    }

    result = organizations_connector.classify_aws_accounts(labeled_accounts=labeled, suffix="_east")

    assert result["production_accounts_east"] == ["123"]
    assert result["development_accounts_east"] == ["456"]


def test_preprocess_aws_organization_uses_helpers(mocker, organizations_connector: _TestAWSOrganizations):
    labeled_accounts = {
        "123": {
            "account_name": "Prod Account",
            "email": "prod@example.com",
            "json_key": "ProdAccount",
            "classifications": ["production"],
        }
    }
    mocker.patch.object(
        organizations_connector,
        "_build_org_units_with_tags",
        return_value={"ou-prod": {"id": "ou-prod", "name": "Prod", "tags": {}}},
    )
    mocker.patch.object(
        organizations_connector,
        "label_aws_accounts",
        return_value=labeled_accounts,
    )
    mocker.patch.object(
        organizations_connector,
        "classify_aws_accounts",
        return_value={"production_accounts": ["123"]},
    )

    class _RootsClient:
        def list_roots(self):
            return {"Roots": [{"Id": "r-root"}]}

    mocker.patch.object(
        organizations_connector,
        "get_aws_client",
        return_value=_RootsClient(),
    )

    context = organizations_connector.preprocess_aws_organization(domains={"prod": "example.com"})

    assert context["organization"]["root_id"] == "r-root"
    assert context["accounts_by_name"]["Prod Account"]["email"] == "prod@example.com"
    assert context["accounts_by_classification"]["production_accounts"] == ["123"]
