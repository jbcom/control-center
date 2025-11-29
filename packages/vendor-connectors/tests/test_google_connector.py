"""Tests for GoogleConnector."""

from unittest.mock import MagicMock, patch

from typing import Any

import pytest
from googleapiclient.errors import HttpError

from vendor_connectors.google import GoogleConnector


def _http_error(status_code: int) -> HttpError:
    """Create a HttpError with the given status for testing."""
    response = MagicMock()
    response.status = status_code
    response.reason = "reason"
    return HttpError(response, b"error")


@pytest.fixture
def google_service_account() -> dict[str, str]:
    """Reusable fake service account payload."""
    return {
        "type": "service_account",
        "client_email": "test@example.iam.gserviceaccount.com",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
        "private_key_id": "key123",
        "project_id": "test-project",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }


class TestGoogleConnector:
    """Test suite for GoogleConnector."""

    def test_init_with_dict_service_account(self, base_connector_kwargs, google_service_account):
        """Test initialization with dictionary service account."""
        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        assert connector.service_account_info == google_service_account
        assert connector._credentials is None

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    def test_credentials_property(self, mock_from_sa, base_connector_kwargs, google_service_account):
        """Test credentials property creates credentials."""
        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        creds = connector.credentials
        assert creds == mock_credentials
        mock_from_sa.assert_called_once()

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    @patch("vendor_connectors.google.build")
    def test_get_service(self, mock_build, mock_from_sa, base_connector_kwargs, google_service_account):
        """Test getting a Google service."""
        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        service = connector.get_service("admin", "directory_v1")
        assert service == mock_service
        mock_build.assert_called_once_with("admin", "directory_v1", credentials=mock_credentials)

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    @patch("vendor_connectors.google.build")
    def test_get_service_caching(self, mock_build, mock_from_sa, base_connector_kwargs, google_service_account):
        """Test that services are cached."""
        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        # Call twice
        service1 = connector.get_service("admin", "directory_v1")
        service2 = connector.get_service("admin", "directory_v1")

        # Build should only be called once
        assert mock_build.call_count == 1
        assert service1 is service2

    @patch.object(GoogleConnector, "get_admin_directory_service")
    def test_get_google_users_filters_and_unhumps(
        self,
        mock_directory_service,
        base_connector_kwargs,
        google_service_account,
    ):
        """Ensure filtering flags match terraform semantics."""

        def make_request(payload: dict[str, Any]) -> MagicMock:
            request = MagicMock()
            request.execute.return_value = payload
            return request

        directory = MagicMock()
        users_resource = MagicMock()
        users_resource.list.side_effect = [
            make_request(
                {
                    "users": [
                        {
                            "primaryEmail": "active@example.com",
                            "orgUnitPath": "/Engineering",
                            "name": {"givenName": "Active", "familyName": "User"},
                        },
                        {
                            "primaryEmail": "bot@example.com",
                            "orgUnitPath": "/Automation/Bots",
                            "name": {"givenName": "Bot", "familyName": "User"},
                        },
                    ],
                    "nextPageToken": "next-token",
                }
            ),
            make_request(
                {
                    "users": [
                        {
                            "primaryEmail": "finance@example.com",
                            "orgUnitPath": "/Finance",
                            "name": {"givenName": "Finance", "familyName": "User"},
                        },
                        {
                            "primaryEmail": "inactive@example.com",
                            "orgUnitPath": "/Engineering",
                            "suspended": True,
                            "name": {"givenName": "Inactive", "familyName": "User"},
                        },
                    ]
                }
            ),
        ]
        directory.users.return_value = users_resource
        mock_directory_service.return_value = directory

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        results = connector.get_google_users(
            allowed_ous=("/Engineering",),
            denied_ous=("/Finance",),
            include_bots=False,
            flatten_name=True,
            unhump_users=True,
            active_only=True,
            domain="example.com",
        )

        assert list(results.keys()) == ["active@example.com"]
        assert results["active@example.com"]["given_name"] == "Active"
        assert "name" not in results["active@example.com"]

    @patch.object(GoogleConnector, "get_groups_settings_service")
    @patch.object(GoogleConnector, "get_admin_directory_service")
    def test_get_google_groups_merges_settings_and_members(
        self,
        mock_directory_service,
        mock_settings_service,
        base_connector_kwargs,
        google_service_account,
    ):
        """Verify group results merge settings, members, and unhump correctly."""

        def make_request(payload: dict[str, Any]) -> MagicMock:
            request = MagicMock()
            request.execute.return_value = payload
            return request

        # Directory mocks
        directory = MagicMock()
        groups_resource = MagicMock()
        groups_resource.list.side_effect = [
            make_request(
                {
                    "groups": [
                        {
                            "email": "eng@example.com",
                            "name": "Engineering",
                        }
                    ]
                }
            )
        ]
        members_resource = MagicMock()
        members_resource.list.side_effect = [
            make_request(
                {
                    "members": [
                        {
                            "email": "member@example.com",
                            "status": "ACTIVE",
                            "type": "USER",
                            "role": "MEMBER",
                        },
                        {
                            "email": "disabled@example.com",
                            "status": "SUSPENDED",
                            "type": "USER",
                        },
                    ]
                }
            )
        ]
        directory.groups.return_value = groups_resource
        directory.members.return_value = members_resource
        mock_directory_service.return_value = directory

        # Settings mock
        settings_api = MagicMock()
        settings_api.get.return_value.execute.return_value = {
            "whoCanJoin": "ALL_IN_DOMAIN_CAN_JOIN"
        }
        mock_settings_service.return_value.groups.return_value = settings_api

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        groups = connector.get_google_groups(
            domain="example.com",
            only_status_for_members="ACTIVE",
            unhump_groups=True,
            members_only=False,
            flatten_members=False,
        )

        assert "eng@example.com" in groups
        group_payload = groups["eng@example.com"]
        assert group_payload["who_can_join"] == "ALL_IN_DOMAIN_CAN_JOIN"
        members = group_payload["members"]
        assert list(members.keys()) == ["member@example.com"]
        assert members["member@example.com"]["status"] == "ACTIVE"

    @patch.object(GoogleConnector, "get_admin_directory_service")
    def test_create_google_user_handles_existing_records(
        self,
        mock_directory_service,
        base_connector_kwargs,
        google_service_account,
    ):
        """Ensure create_google_user inserts or updates appropriately."""

        directory = MagicMock()
        users_resource = MagicMock()
        directory.users.return_value = users_resource
        mock_directory_service.return_value = directory

        users_resource.get.side_effect = _http_error(404)
        users_resource.insert.return_value.execute.return_value = {"primaryEmail": "new@example.com"}

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        created = connector.create_google_user(
            given_name="First",
            family_name="Last",
            user_password="secret",
            primary_email="new@example.com",
        )
        assert created["primaryEmail"] == "new@example.com"
        assert users_resource.insert.called

        # Existing record path with update
        users_resource.get.side_effect = None
        users_resource.get.return_value.execute.return_value = {"primaryEmail": "new@example.com"}
        users_resource.update.return_value.execute.return_value = {"primaryEmail": "new@example.com", "name": {"givenName": "First"}}

        updated = connector.create_google_user(
            given_name="First",
            family_name="Last",
            user_password="secret",
            primary_email="new@example.com",
            update_if_exists=True,
        )
        assert updated["primaryEmail"] == "new@example.com"
        assert users_resource.update.called

    @patch.object(GoogleConnector, "get_admin_directory_service")
    def test_create_google_group_handles_existing_records(
        self,
        mock_directory_service,
        base_connector_kwargs,
        google_service_account,
    ):
        """Ensure create_google_group mirrors terraform behaviour."""

        directory = MagicMock()
        groups_resource = MagicMock()
        directory.groups.return_value = groups_resource
        mock_directory_service.return_value = directory

        groups_resource.get.side_effect = _http_error(404)
        groups_resource.insert.return_value.execute.return_value = {"email": "team@example.com"}

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        created = connector.create_google_group(
            group_email="team@example.com",
            group_name="Team",
        )
        assert created["email"] == "team@example.com"

        groups_resource.get.side_effect = None
        groups_resource.get.return_value.execute.return_value = {"email": "team@example.com"}
        groups_resource.update.return_value.execute.return_value = {"email": "team@example.com", "name": "Updated"}

        updated = connector.create_google_group(
            group_email="team@example.com",
            group_name="Team",
            update_if_exists=True,
        )
        assert updated["email"] == "team@example.com"
        assert groups_resource.update.called

    def test_get_google_client_for_user_reuses_credentials(
        self,
        base_connector_kwargs,
        google_service_account,
    ):
        """get_google_client_for_user should clone connector state with a subject."""

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        user_connector = connector.get_google_client_for_user("person@example.com")
        assert user_connector.subject == "person@example.com"
        assert user_connector.scopes == connector.scopes
        assert user_connector.service_account_info == connector.service_account_info
        assert user_connector is not connector

    def test_default_scopes_include_terraform_permissions(
        self,
        base_connector_kwargs,
        google_service_account,
    ):
        """Regression guard that CalVer scopes remain expansive."""

        connector = GoogleConnector(
            service_account_info=google_service_account,
            **base_connector_kwargs,
        )

        assert "https://www.googleapis.com/auth/cloudkms" in connector.scopes
        assert "https://www.googleapis.com/auth/cloud-billing" in connector.scopes
