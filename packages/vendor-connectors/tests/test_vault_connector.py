"""Tests for VaultConnector."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from cloud_connectors.vault import VaultConnector


class TestVaultConnector:
    """Test suite for VaultConnector."""

    def test_init(self, base_connector_kwargs):
        """Test initialization."""
        connector = VaultConnector(
            vault_address="https://vault.example.com",
            vault_namespace="test-namespace",
            vault_token="test-token",
            **base_connector_kwargs,
        )

        assert connector.vault_address == "https://vault.example.com"
        assert connector.vault_namespace == "test-namespace"
        assert connector.vault_token == "test-token"
        assert connector._vault_client is None

    @patch("cloud_connectors.vault.hvac.Client")
    def test_vault_client_with_token(self, mock_hvac_class, base_connector_kwargs):
        """Test getting vault client with token authentication."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.lookup_token.return_value = {"expire_time": "2024-12-31T23:59:59Z"}
        mock_hvac_class.return_value = mock_client

        connector = VaultConnector(
            vault_address="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        client = connector.vault_client
        assert client == mock_client
        mock_hvac_class.assert_called()

    @patch("cloud_connectors.vault.hvac.Client")
    def test_vault_client_with_approle(self, mock_hvac_class, base_connector_kwargs):
        """Test getting vault client with AppRole authentication."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.auth.approle.login.return_value = {"auth": {"policies": ["default"], "lease_duration": 3600}}
        mock_client.lookup_token.return_value = {"expire_time": "2024-12-31T23:59:59Z"}
        mock_hvac_class.return_value = mock_client

        # Create connector with env inputs
        inputs = {
            "VAULT_ADDR": "https://vault.example.com",
            "VAULT_ROLE_ID": "test-role-id",
            "VAULT_SECRET_ID": "test-secret-id",
        }

        connector = VaultConnector(vault_address="https://vault.example.com", inputs=inputs, **base_connector_kwargs)

        # Mock is_authenticated to return False first, then True after AppRole login
        mock_client.is_authenticated.side_effect = [False, True]

        client = connector.vault_client
        assert client == mock_client

    def test_is_token_valid(self, base_connector_kwargs):
        """Test token validity check."""
        connector = VaultConnector(
            vault_address="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        # No expiration set
        assert connector._is_token_valid() is False

        # Set future expiration
        connector._vault_token_expiration = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert connector._is_token_valid() is True

        # Set past expiration
        connector._vault_token_expiration = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert connector._is_token_valid() is False

    @patch("cloud_connectors.vault.hvac.Client")
    def test_get_vault_client_classmethod(self, mock_hvac_class, base_connector_kwargs):
        """Test class method for getting vault client."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.lookup_token.return_value = {"expire_time": "2024-12-31T23:59:59Z"}
        mock_hvac_class.return_value = mock_client

        client = VaultConnector.get_vault_client(
            vault_address="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        assert client == mock_client
