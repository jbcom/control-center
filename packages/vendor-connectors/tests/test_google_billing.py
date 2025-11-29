"""Tests for Google Billing mixin helpers."""

from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from vendor_connectors.google.billing import GoogleBillingMixin


class _StubLogger:
    def info(self, *args, **kwargs):  # pragma: no cover - pass-through logger stub
        pass

    def warning(self, *args, **kwargs):  # pragma: no cover
        pass


class _ImmediateResponse:
    def __init__(self, response: dict[str, Any]):
        self._response = response

    def execute(self) -> dict[str, Any]:
        return self._response


class _StubProjectsAPI:
    def __init__(self):
        self.update_calls: list[dict[str, Any]] = []

    def updateBillingInfo(self, name: str, body: dict[str, Any]):
        self.update_calls.append({"name": name, "body": body})
        return _ImmediateResponse({"name": name, **body})


class _StubBillingAccountProjectsAPI:
    def __init__(self, responses: Iterable[dict[str, Any]]):
        self._responses = deque(responses)
        self.list_calls: list[dict[str, Any]] = []

    def list(self, **params):
        self.list_calls.append(params)
        return _ImmediateResponse(self._responses.popleft())


class _StubBillingAccountsAPI:
    def __init__(
        self,
        account_responses: Iterable[dict[str, Any]],
        project_responses: Iterable[dict[str, Any]],
    ):
        self._account_responses = deque(account_responses)
        self.list_calls: list[dict[str, Any]] = []
        self._projects_api = _StubBillingAccountProjectsAPI(project_responses)

    def list(self, **params):
        self.list_calls.append(params)
        return _ImmediateResponse(self._account_responses.popleft())

    def projects(self):
        return self._projects_api


class _StubBillingService:
    def __init__(
        self,
        account_responses: Iterable[dict[str, Any]],
        project_responses: Iterable[dict[str, Any]],
    ):
        self._accounts_api = _StubBillingAccountsAPI(account_responses, project_responses)
        self._projects_api = _StubProjectsAPI()

    def billingAccounts(self):
        return self._accounts_api

    def projects(self):
        return self._projects_api


class _TestGoogleBilling(GoogleBillingMixin):
    def __init__(self, service: _StubBillingService):
        self.logger = _StubLogger()
        self._service = service

    def get_billing_service(self):
        return self._service


def test_list_billing_accounts_paginates_and_unhumps():
    service = _StubBillingService(
        account_responses=[
            {
                "billingAccounts": [
                    {"name": "billingAccounts/ABC", "displayName": "Primary"},
                ],
                "nextPageToken": "token-1",
            },
            {
                "billingAccounts": [
                    {"name": "billingAccounts/DEF", "displayName": "Secondary"},
                ],
            },
        ],
        project_responses=[],
    )
    connector = _TestGoogleBilling(service)

    accounts = connector.list_billing_accounts(filter_query="parent:organizations/1", unhump_accounts=True)

    assert [acct["name"] for acct in accounts] == ["billingAccounts/ABC", "billingAccounts/DEF"]
    # Ensure snake_case conversion applied
    assert accounts[0]["display_name"] == "Primary"
    assert service.billingAccounts().list_calls == [
        {"filter": "parent:organizations/1"},
        {"filter": "parent:organizations/1", "pageToken": "token-1"},
    ]


def test_update_project_billing_info_prefixes_account_name():
    service = _StubBillingService(account_responses=[], project_responses=[])
    connector = _TestGoogleBilling(service)

    response = connector.update_project_billing_info("demo-project", "1234-ABCD")

    assert response["billingAccountName"] == "billingAccounts/1234-ABCD"
    assert service.projects().update_calls == [
        {
            "name": "projects/demo-project",
            "body": {"billingAccountName": "billingAccounts/1234-ABCD"},
        }
    ]


def test_disable_project_billing_sets_empty_account():
    service = _StubBillingService(account_responses=[], project_responses=[])
    connector = _TestGoogleBilling(service)

    response = connector.disable_project_billing("demo-project")

    assert response["billingAccountName"] == ""
    assert service.projects().update_calls[-1] == {
        "name": "projects/demo-project",
        "body": {"billingAccountName": ""},
    }


def test_list_billing_account_projects_handles_prefixing():
    service = _StubBillingService(
        account_responses=[],
        project_responses=[
            {
                "projectBillingInfo": [{"projectId": "alpha"}],
                "nextPageToken": "p1",
            },
            {
                "projectBillingInfo": [{"projectId": "beta"}],
            },
        ],
    )
    connector = _TestGoogleBilling(service)

    projects = connector.list_billing_account_projects("123456-AAAA", unhump_projects=True)

    assert [proj["project_id"] for proj in projects] == ["alpha", "beta"]
    assert service.billingAccounts().projects().list_calls == [
        {"name": "billingAccounts/123456-AAAA"},
        {"name": "billingAccounts/123456-AAAA", "pageToken": "p1"},
    ]
