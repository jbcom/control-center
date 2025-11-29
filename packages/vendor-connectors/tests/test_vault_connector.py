"""Tests for VaultConnector."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from hvac.exceptions import VaultError

from vendor_connectors.vault import VaultConnector


class TestVaultConnector:
    """Test suite for VaultConnector."""

    def test_init(self, base_connector_kwargs):
        """Test initialization."""
        connector = VaultConnector(
            vault_url="https://vault.example.com",
            vault_namespace="test-namespace",
            vault_token="test-token",
            **base_connector_kwargs,
        )

        assert connector.vault_url == "https://vault.example.com"
        assert connector.vault_namespace == "test-namespace"
        assert connector.vault_token == "test-token"
        assert connector._vault_client is None

    @patch("vendor_connectors.vault.hvac.Client")
    def test_vault_client_with_token(self, mock_hvac_class, base_connector_kwargs):
        """Test getting vault client with token authentication."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.auth.token.lookup_self.return_value = {"data": {"expire_time": "2024-12-31T23:59:59Z"}}
        mock_hvac_class.return_value = mock_client

        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        client = connector.vault_client
        assert client == mock_client
        mock_hvac_class.assert_called()

    def test_is_token_valid(self, base_connector_kwargs):
        """Test token validity check."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        # No expiration set
        assert connector._is_token_valid() is False

        # Set future expiration
        connector._vault_token_expiration = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert connector._is_token_valid() is True

        # Set past expiration
        connector._vault_token_expiration = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert connector._is_token_valid() is False

    @patch("vendor_connectors.vault.hvac.Client")
    def test_get_vault_client_classmethod(self, mock_hvac_class, base_connector_kwargs):
        """Test class method for getting vault client."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.auth.token.lookup_self.return_value = {"data": {"expire_time": "2024-12-31T23:59:59Z"}}
        mock_hvac_class.return_value = mock_client

        client = VaultConnector.get_vault_client(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        assert client == mock_client

    def test_list_secrets_recurses_directories(self, base_connector_kwargs):
        """List secrets should traverse nested directories from root."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        kv_v2 = mock_client.secrets.kv.v2

        def list_side_effect(path, mount_point):
            listings = {
                "": {"data": {"keys": ["finance/", "shared"]}},
                "finance/": {"data": {"keys": ["prod/", "dev"]}},
                "finance/prod/": {"data": {"keys": ["db"]}},
            }
            return listings.get(path, {"data": {"keys": []}})

        kv_v2.list_secrets.side_effect = list_side_effect

        def read_side_effect(path, mount_point):
            data_map = {
                "shared": {"data": {"data": {"value": "shared"}}},
                "finance/dev": {"data": {"data": {"value": "dev"}}},
                "finance/prod/db": {"data": {"data": {"value": "db"}}},
            }
            if path not in data_map:
                raise VaultError(f"missing {path}")
            return data_map[path]

        kv_v2.read_secret_version.side_effect = read_side_effect

        secrets = connector.list_secrets()

        assert secrets == {
            "shared": {"value": "shared"},
            "finance/dev": {"value": "dev"},
            "finance/prod/db": {"value": "db"},
        }
        assert kv_v2.list_secrets.call_args_list[0].kwargs["path"] == ""

    def test_list_secrets_handles_invalid_root(self, base_connector_kwargs):
        """Invalid root paths should return an empty dict instead of raising."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.kv.v2.list_secrets.side_effect = VaultError("invalid")

        secrets = connector.list_secrets(root_path="does/not/exist")

        assert secrets == {}
        mock_client.secrets.kv.v2.list_secrets.assert_called_once_with(
            path="does/not/exist",
            mount_point="secret",
        )
