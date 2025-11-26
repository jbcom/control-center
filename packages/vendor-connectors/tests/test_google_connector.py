"""Tests for GoogleConnector."""

from unittest.mock import MagicMock, patch

from vendor_connectors.google import GoogleConnector


class TestGoogleConnector:
    """Test suite for GoogleConnector."""

    def test_init_with_dict_service_account(self, base_connector_kwargs):
        """Test initialization with dictionary service account."""
        service_account = {
            "type": "service_account",
            "client_email": "test@example.iam.gserviceaccount.com",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
            "private_key_id": "key123",
            "project_id": "test-project",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        connector = GoogleConnector(
            service_account_info=service_account,
            **base_connector_kwargs,
        )

        assert connector.service_account_info == service_account
        assert connector._credentials is None

    @patch("vendor_connectors.google.service_account.Credentials.from_service_account_info")
    def test_credentials_property(self, mock_from_sa, base_connector_kwargs):
        """Test credentials property creates credentials."""
        service_account = {
            "type": "service_account",
            "client_email": "test@example.iam.gserviceaccount.com",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
            "private_key_id": "key123",
            "project_id": "test-project",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

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
        service_account = {
            "type": "service_account",
            "client_email": "test@example.iam.gserviceaccount.com",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
            "private_key_id": "key123",
            "project_id": "test-project",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

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
        service_account = {
            "type": "service_account",
            "client_email": "test@example.iam.gserviceaccount.com",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
            "private_key_id": "key123",
            "project_id": "test-project",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

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
