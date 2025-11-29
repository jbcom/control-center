"""Tests for VaultConnector."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
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

    def test_list_secrets_rejects_path_traversal(self, base_connector_kwargs):
        """Ensure list_secrets rejects path traversal in root_path."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        # Should reject path traversal attempts
        with pytest.raises(ValueError, match="invalid characters"):
            connector.list_secrets(root_path="../../../etc/passwd")

        with pytest.raises(ValueError, match="invalid characters"):
            connector.list_secrets(root_path="secrets/../admin")

        # Should reject null bytes
        with pytest.raises(ValueError, match="invalid characters"):
            connector.list_secrets(root_path="secrets\x00admin")

    def test_list_aws_iam_roles_filters_prefix(self, base_connector_kwargs):
        """Ensure AWS IAM roles can be listed and filtered by prefix."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.aws.list_roles.return_value = {"data": {"keys": ["prod-sync", "dev-sync"]}}

        roles = connector.list_aws_iam_roles(name_prefix="prod")

        assert roles == ["prod-sync"]
        mock_client.secrets.aws.list_roles.assert_called_once_with(mount_point="aws")

    def test_list_aws_iam_roles_handles_errors(self, base_connector_kwargs):
        """Vault errors while listing roles should return an empty list."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.aws.list_roles.side_effect = VaultError("boom")

        roles = connector.list_aws_iam_roles()

        assert roles == []

    def test_get_aws_iam_role_returns_data(self, base_connector_kwargs):
        """get_aws_iam_role should fetch role metadata."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.aws.read_role.return_value = {"data": {"arn": "arn:aws:iam::123:role/prod"}}

        role_data = connector.get_aws_iam_role(role_name="prod")

        assert role_data == {"arn": "arn:aws:iam::123:role/prod"}
        mock_client.secrets.aws.read_role.assert_called_once_with(name="prod", mount_point="aws")

    def test_get_aws_iam_role_handles_errors(self, base_connector_kwargs):
        """Vault failures when fetching role metadata should return None."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.aws.read_role.side_effect = VaultError("missing")

        assert connector.get_aws_iam_role(role_name="missing") is None

    def test_generate_aws_credentials_success(self, base_connector_kwargs):
        """generate_aws_credentials should return the generated credential payload."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.aws.generate_credentials.return_value = {
            "data": {"access_key": "AKIA", "secret_key": "SECRET", "security_token": "TOKEN"}
        }

        credentials = connector.generate_aws_credentials(role_name="prod", ttl="1h", credential_type="sts")

        assert credentials["access_key"] == "AKIA"
        mock_client.secrets.aws.generate_credentials.assert_called_once_with(
            name="prod",
            mount_point="aws",
            ttl="1h",
            type="sts",
        )

    def test_generate_aws_credentials_error(self, base_connector_kwargs):
        """Vault errors while generating credentials should raise RuntimeError."""
        connector = VaultConnector(
            vault_url="https://vault.example.com", vault_token="test-token", **base_connector_kwargs
        )

        mock_client = MagicMock()
        connector._vault_client = mock_client
        connector._vault_token_expiration = datetime(2099, 1, 1, tzinfo=timezone.utc)

        mock_client.secrets.aws.generate_credentials.side_effect = VaultError("boom")

        with pytest.raises(RuntimeError):
            connector.generate_aws_credentials(role_name="prod")
