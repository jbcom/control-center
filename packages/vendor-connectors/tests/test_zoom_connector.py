"""Tests for ZoomConnector."""
import pytest
from unittest.mock import MagicMock, patch

from cloud_connectors.zoom import ZoomConnector


class TestZoomConnector:
    """Test suite for ZoomConnector."""

    def test_init(self, base_connector_kwargs):
        """Test initialization."""
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs
        )
        
        assert connector.client_id == "test-client-id"
        assert connector.client_secret == "test-client-secret"
        assert connector.account_id == "test-account-id"

    @patch('cloud_connectors.zoom.requests.post')
    def test_get_access_token_success(self, mock_post, base_connector_kwargs):
        """Test successful access token retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs
        )
        
        token = connector.get_access_token()
        assert token == "test-access-token"
        mock_post.assert_called_once()

    @patch('cloud_connectors.zoom.requests.post')
    def test_get_access_token_failure(self, mock_post, base_connector_kwargs):
        """Test failed access token retrieval."""
        mock_post.side_effect = Exception("Connection error")
        
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs
        )
        
        with pytest.raises(RuntimeError, match="Failed to get Zoom access token"):
            connector.get_access_token()

    @patch('cloud_connectors.zoom.requests.get')
    @patch('cloud_connectors.zoom.requests.post')
    def test_get_zoom_users(self, mock_post, mock_get, base_connector_kwargs):
        """Test getting Zoom users."""
        # Mock access token
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response
        
        # Mock users response
        mock_users_response = MagicMock()
        mock_users_response.json.return_value = {
            "users": [
                {"email": "user1@example.com", "id": "123", "first_name": "User", "last_name": "One"},
                {"email": "user2@example.com", "id": "456", "first_name": "User", "last_name": "Two"}
            ],
            "next_page_token": None
        }
        mock_users_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_users_response
        
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs
        )
        
        users = connector.get_zoom_users()
        assert "user1@example.com" in users
        assert "user2@example.com" in users
        assert len(users) == 2

    @patch('cloud_connectors.zoom.requests.delete')
    @patch('cloud_connectors.zoom.requests.post')
    def test_remove_zoom_user(self, mock_post, mock_delete, base_connector_kwargs):
        """Test removing a Zoom user."""
        # Mock access token
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response
        
        # Mock delete response
        mock_delete_response = MagicMock()
        mock_delete_response.raise_for_status = MagicMock()
        mock_delete.return_value = mock_delete_response
        
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs
        )
        
        connector.remove_zoom_user("user@example.com")
        mock_delete.assert_called_once()

    @patch('cloud_connectors.zoom.requests.post')
    def test_create_zoom_user(self, mock_post, base_connector_kwargs):
        """Test creating a Zoom user."""
        # Mock access token on first call
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        
        # Mock create user on second call
        mock_create_response = MagicMock()
        mock_create_response.raise_for_status = MagicMock()
        
        mock_post.side_effect = [mock_token_response, mock_create_response]
        
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs
        )
        
        result = connector.create_zoom_user("newuser@example.com", "New", "User")
        assert result is True
        assert mock_post.call_count == 2
