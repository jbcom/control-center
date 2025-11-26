"""Tests for GoogleConnector."""
import pytest
from unittest.mock import MagicMock, patch

from cloud_connectors.google import GoogleConnector


class TestGoogleConnector:
    """Test suite for GoogleConnector."""

    def test_init_with_dict_service_account(self, base_connector_kwargs):
        """Test initialization with dictionary service account."""
        service_account = {
            "client_email": "test@example.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "project_id": "test-project"
        }
        
        connector = GoogleConnector(
            scopes=["https://www.googleapis.com/auth/admin.directory.user"],
            service_account_file=service_account,
            **base_connector_kwargs
        )
        
        assert connector.scopes == ["https://www.googleapis.com/auth/admin.directory.user"]
        assert connector.service_account_file == service_account
        assert connector.subject == "test@example.com"

    def test_init_with_json_string(self, base_connector_kwargs):
        """Test initialization with JSON string service account."""
        service_account_json = '{"client_email": "test@example.com", "private_key": "-----BEGIN PRIVATE KEY-----\\ntest\\n-----END PRIVATE KEY-----", "project_id": "test-project"}'
        
        connector = GoogleConnector(
            scopes=["https://www.googleapis.com/auth/admin.directory.user"],
            service_account_file=service_account_json,
            **base_connector_kwargs
        )
        
        assert connector.subject == "test@example.com"

    def test_init_missing_required_fields(self, base_connector_kwargs):
        """Test initialization with missing required fields."""
        service_account = {
            "client_email": "test@example.com"
        }
        
        with pytest.raises(ValueError, match="missing required fields"):
            GoogleConnector(
                scopes=["https://www.googleapis.com/auth/admin.directory.user"],
                service_account_file=service_account,
                **base_connector_kwargs
            )

    @patch('cloud_connectors.google.service_account.Credentials.from_service_account_info')
    @patch('cloud_connectors.google.googleapiclient.discovery.build')
    def test_get_service_workspace(self, mock_build, mock_from_sa, base_connector_kwargs):
        """Test getting workspace service."""
        service_account = {
            "client_email": "test@example.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "project_id": "test-project"
        }
        
        mock_credentials = MagicMock()
        mock_from_sa.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        connector = GoogleConnector(
            scopes=["https://www.googleapis.com/auth/admin.directory.user"],
            service_account_file=service_account,
            **base_connector_kwargs
        )
        
        service = connector.get_service("admin", "directory_v1")
        assert service == mock_service

    def test_is_cloud_service(self, base_connector_kwargs):
        """Test cloud service detection."""
        service_account = {
            "client_email": "test@example.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "project_id": "test-project"
        }
        
        connector = GoogleConnector(
            scopes=["https://www.googleapis.com/auth/admin.directory.user"],
            service_account_file=service_account,
            **base_connector_kwargs
        )
        
        assert connector._is_cloud_service("billing", "v1") is True
        assert connector._is_cloud_service("admin", "directory_v1") is False
