"""Tests for GoogleConnector."""

from unittest.mock import MagicMock, patch

from vendor_connectors.google import GoogleConnector


def _service_account():
    """Return a reusable service account payload."""
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


class _StubRequest:
    """Simple request stub for the Google Admin SDK."""

    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _StubCollection:
    """Collection stub that yields predefined response pages."""

    def __init__(self, pages):
        self._pages = pages
        self._index = 0

    def list(self, **_):
        payload = self._pages[self._index]
        self._index += 1
        return _StubRequest(payload)


class _StubAdminDirectoryService:
    """Admin Directory service stub exposing users() and groups()."""

    def __init__(self, *, user_pages=None, group_pages=None):
        if user_pages is None:
            user_pages = [{"users": []}]
        if group_pages is None:
            group_pages = [{"groups": []}]

        self._user_collection = _StubCollection(user_pages)
        self._group_collection = _StubCollection(group_pages)

    def users(self):
        return self._user_collection

    def groups(self):
        return self._group_collection


class TestGoogleConnector:
    """Test suite for GoogleConnector."""

    def test_init_with_dict_service_account(self, base_connector_kwargs):
        """Test initialization with dictionary service account."""
        service_account = _service_account()

        connector = GoogleConnector(
            service_account_info=service_account,
            **base_connector_kwargs,
        )

        assert connector.service_account_info == service_account
        assert connector._credentials is None

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    def test_credentials_property(self, mock_from_sa, base_connector_kwargs):
        """Test credentials property creates credentials."""
        service_account = _service_account()

        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials

        connector = GoogleConnector(
            service_account_info=service_account,
            **base_connector_kwargs,
        )

        creds = connector.credentials
        assert creds == mock_credentials
        mock_from_sa.assert_called_once()

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    @patch("vendor_connectors.google.build")
    def test_get_service(self, mock_build, mock_from_sa, base_connector_kwargs):
        """Test getting a Google service."""
        service_account = _service_account()

        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        connector = GoogleConnector(
            service_account_info=service_account,
            **base_connector_kwargs,
        )

        service = connector.get_service("admin", "directory_v1")
        assert service == mock_service
        mock_build.assert_called_once_with("admin", "directory_v1", credentials=mock_credentials)

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    @patch("vendor_connectors.google.build")
    def test_get_service_caching(self, mock_build, mock_from_sa, base_connector_kwargs):
        """Test that services are cached."""
        service_account = _service_account()

        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        connector = GoogleConnector(
            service_account_info=service_account,
            **base_connector_kwargs,
        )

        # Call twice
        service1 = connector.get_service("admin", "directory_v1")
        service2 = connector.get_service("admin", "directory_v1")

        # Build should only be called once
        assert mock_build.call_count == 1
        assert service1 is service2

    @patch.object(GoogleConnector, "get_admin_directory_service")
    def test_list_users_filters_and_transforms(self, mock_get_service, base_connector_kwargs):
        """Ensure list_users applies filtering, flattening, and keying."""
        user_pages = [
            {
                "users": [
                    {
                        "primaryEmail": "bot@example.com",
                        "orgUnitPath": "/Bots",
                        "isBot": True,
                        "name": {"fullName": "Bot Account", "givenName": "Bot", "familyName": "Account"},
                    },
                    {
                        "primaryEmail": "engineer@example.com",
                        "orgUnitPath": "/Engineering",
                        "name": {"fullName": "Eng One", "givenName": "Eng", "familyName": "One"},
                    },
                ],
                "nextPageToken": "token-1",
            },
            {
                "users": [
                    {
                        "primaryEmail": "suspended@example.com",
                        "orgUnitPath": "/Engineering",
                        "suspended": True,
                        "name": {"fullName": "Susp User", "givenName": "Susp", "familyName": "User"},
                    },
                    {
                        "primaryEmail": "sales@example.com",
                        "orgUnitPath": "/Sales",
                        "name": {"fullName": "Sales User", "givenName": "Sales", "familyName": "User"},
                    },
                ],
            },
        ]
        mock_get_service.return_value = _StubAdminDirectoryService(user_pages=user_pages)

        connector = GoogleConnector(service_account_info=_service_account(), **base_connector_kwargs)
        result = connector.list_users(
            ou_allow_list=["/Engineering"],
            ou_deny_list=["/Sales"],
            flatten_names=True,
            key_by_email=True,
        )

        assert "bot@example.com" not in result
        assert "suspended@example.com" not in result
        assert "sales@example.com" not in result
        assert result["engineer@example.com"]["full_name"] == "Eng One"
        assert result["engineer@example.com"]["given_name"] == "Eng"
        assert result["engineer@example.com"]["family_name"] == "One"

    @patch.object(GoogleConnector, "get_admin_directory_service")
    def test_list_groups_key_by_email_and_filters(self, mock_get_service, base_connector_kwargs):
        """Ensure list_groups supports filtering and keying similar to list_users."""
        group_pages = [
            {
                "groups": [
                    {"email": "bots@example.com", "orgUnitPath": "/Bots", "type": "BOT"},
                    {
                        "email": "keepers@example.com",
                        "orgUnitPath": "/Engineering",
                        "suspended": True,
                    },
                    {"primaryEmail": "team@example.com", "orgUnitPath": "/Engineering"},
                ]
            }
        ]
        mock_get_service.return_value = _StubAdminDirectoryService(group_pages=group_pages)

        connector = GoogleConnector(service_account_info=_service_account(), **base_connector_kwargs)
        result = connector.list_groups(
            ou_deny_list=["/Bots"],
            include_suspended=True,
            key_by_email=True,
        )

        assert "bots@example.com" not in result
        assert "keepers@example.com" in result
        assert result["keepers@example.com"]["suspended"] is True
        assert "team@example.com" in result
        assert result["team@example.com"]["primaryEmail"] == "team@example.com"
