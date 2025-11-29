"""Tests for AWSConnector."""

from unittest.mock import MagicMock, Mock, call, patch

import pytest
from botocore.exceptions import ClientError

from vendor_connectors.aws import AWSConnector


class TestAWSConnector:
    """Test suite for AWSConnector."""

    def test_init_without_role(self, base_connector_kwargs):
        """Test initialization without execution role."""
        connector = AWSConnector(**base_connector_kwargs)
        assert connector.execution_role_arn is None
        assert connector.aws_sessions == {}
        assert connector.default_aws_session is not None

    def test_init_with_role(self, base_connector_kwargs):
        """Test initialization with execution role."""
        role_arn = "arn:aws:iam::123456789012:role/TestRole"
        connector = AWSConnector(execution_role_arn=role_arn, **base_connector_kwargs)
        assert connector.execution_role_arn == role_arn

    @patch("vendor_connectors.aws.boto3.Session")
    def test_assume_role_success(self, mock_session_class, base_connector_kwargs):
        """Test successful role assumption."""
        mock_sts_client = MagicMock()
        mock_sts_client.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "test-access-key",
                "SecretAccessKey": "test-secret-key",
                "SessionToken": "test-session-token",
                "Expiration": Mock(isoformat=lambda: "2024-12-31T23:59:59Z"),
            }
        }

        mock_default_session = MagicMock()
        mock_default_session.client.return_value = mock_sts_client
        mock_session_class.return_value = mock_default_session

        connector = AWSConnector(**base_connector_kwargs)
        connector.default_aws_session = mock_default_session

        role_arn = "arn:aws:iam::123456789012:role/TestRole"
        connector.assume_role(role_arn, "test-session")

        mock_sts_client.assume_role.assert_called_once_with(RoleArn=role_arn, RoleSessionName="test-session")

    @patch("vendor_connectors.aws.boto3.Session")
    def test_assume_role_failure(self, mock_session_class, base_connector_kwargs):
        """Test failed role assumption."""
        mock_sts_client = MagicMock()
        mock_sts_client.assume_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Not authorized"}}, "AssumeRole"
        )

        mock_default_session = MagicMock()
        mock_default_session.client.return_value = mock_sts_client
        mock_session_class.return_value = mock_default_session

        connector = AWSConnector(**base_connector_kwargs)
        connector.default_aws_session = mock_default_session

        role_arn = "arn:aws:iam::123456789012:role/TestRole"

        with pytest.raises(RuntimeError, match="Failed to assume role"):
            connector.assume_role(role_arn, "test-session")

    def test_get_aws_session_default(self, base_connector_kwargs):
        """Test getting default AWS session."""
        connector = AWSConnector(**base_connector_kwargs)
        session = connector.get_aws_session()
        assert session == connector.default_aws_session

    def test_create_standard_retry_config(self):
        """Test creating standard retry configuration."""
        config = AWSConnector.create_standard_retry_config(max_attempts=5)
        assert config.retries["max_attempts"] == 5
        assert config.retries["mode"] == "standard"

    @patch("vendor_connectors.aws.boto3.Session")
    def test_get_aws_client(self, mock_session_class, base_connector_kwargs):
        """Test getting AWS client."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        connector = AWSConnector(**base_connector_kwargs)
        connector.default_aws_session = mock_session

        client = connector.get_aws_client("s3")

        assert client == mock_client
        mock_session.client.assert_called_once()

    @patch("vendor_connectors.aws.boto3.Session")
    def test_get_aws_resource(self, mock_session_class, base_connector_kwargs):
        """Test getting AWS resource."""
        mock_session = MagicMock()
        mock_resource = MagicMock()
        mock_session.resource.return_value = mock_resource
        mock_session_class.return_value = mock_session

        connector = AWSConnector(**base_connector_kwargs)
        connector.default_aws_session = mock_session

        resource = connector.get_aws_resource("s3")

        assert resource == mock_resource
        mock_session.resource.assert_called_once()

    def test_list_secrets_returns_arns_with_filters(self, base_connector_kwargs):
        """Ensure listing secrets returns ARNs when not fetching values."""
        connector = AWSConnector(**base_connector_kwargs)
        mock_secretsmanager = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "SecretList": [
                    {"Name": "/vendors/foo", "ARN": "arn:foo"},
                    {"Name": "/vendors/bar", "ARN": "arn:bar"},
                ]
            }
        ]
        mock_secretsmanager.get_paginator.return_value = mock_paginator
        connector.get_aws_client = MagicMock(return_value=mock_secretsmanager)

        filters = [{"Key": "description", "Values": ["prod"]}]
        secrets = connector.list_secrets(filters=filters, name_prefix="/vendors/")

        assert secrets == {"/vendors/foo": "arn:foo", "/vendors/bar": "arn:bar"}
        connector.get_aws_client.assert_called_once_with(
            client_name="secretsmanager",
            execution_role_arn=None,
            role_session_name=None,
        )
        mock_paginator.paginate.assert_called_once_with(
            IncludePlannedDeletion=False,
            Filters=[
                {"Key": "description", "Values": ["prod"]},
                {"Key": "name", "Values": ["/vendors/"]},
            ],
        )

    def test_list_secrets_fetches_values_and_skips_empty(self, base_connector_kwargs):
        """Ensure fetching secret values respects skip_empty_secrets."""
        connector = AWSConnector(execution_role_arn="arn:aws:iam::123:role/default", **base_connector_kwargs)

        mock_secretsmanager = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "SecretList": [
                    {"Name": "secret/a", "ARN": "arn:a"},
                    {"Name": "secret/b", "ARN": "arn:b"},
                    {"Name": "secret/c", "ARN": "arn:c"},
                ]
            }
        ]
        mock_secretsmanager.get_paginator.return_value = mock_paginator
        connector.get_aws_client = MagicMock(return_value=mock_secretsmanager)

        with (
            patch.object(AWSConnector, "get_secret", side_effect=["value-a", None, "value-c"]) as mock_get_secret,
            patch("vendor_connectors.aws.is_nothing", side_effect=lambda value: value in (None, "", {})),
        ):
            secrets = connector.list_secrets(
                get_secret_values=True,
                skip_empty_secrets=True,
                execution_role_arn="arn:aws:iam::789:role/override",
                role_session_name="session",
            )

        assert secrets == {"secret/a": "value-a", "secret/c": "value-c"}
        connector.get_aws_client.assert_called_once_with(
            client_name="secretsmanager",
            execution_role_arn="arn:aws:iam::789:role/override",
            role_session_name="session",
        )
        mock_paginator.paginate.assert_called_once_with(IncludePlannedDeletion=False)
        mock_get_secret.assert_has_calls(
            [
                call(
                    secret_id="arn:a",
                    execution_role_arn="arn:aws:iam::789:role/override",
                    role_session_name="session",
                    secretsmanager=mock_secretsmanager,
                ),
                call(
                    secret_id="arn:b",
                    execution_role_arn="arn:aws:iam::789:role/override",
                    role_session_name="session",
                    secretsmanager=mock_secretsmanager,
                ),
                call(
                    secret_id="arn:c",
                    execution_role_arn="arn:aws:iam::789:role/override",
                    role_session_name="session",
                    secretsmanager=mock_secretsmanager,
                ),
            ]
        )

    def test_list_secrets_rejects_path_traversal(self, base_connector_kwargs):
        """Ensure list_secrets rejects path traversal in name_prefix."""
        import pytest

        connector = AWSConnector(**base_connector_kwargs)

        # Should reject path traversal attempts
        with pytest.raises(ValueError, match="invalid characters"):
            connector.list_secrets(name_prefix="../../../etc/passwd")

        with pytest.raises(ValueError, match="invalid characters"):
            connector.list_secrets(name_prefix="secrets/../admin")

        # Should reject null bytes
        with pytest.raises(ValueError, match="invalid characters"):
            connector.list_secrets(name_prefix="secrets\x00admin")

    def test_create_secret_with_tags_and_description(self, base_connector_kwargs):
        """Ensure create_secret builds payload and sends to AWS."""
        connector = AWSConnector(**base_connector_kwargs)
        mock_client = MagicMock()
        mock_client.create_secret.return_value = {"ARN": "arn:secret:test"}
        connector.get_aws_client = MagicMock(return_value=mock_client)

        response = connector.create_secret(
            name="/vendors/test",
            secret_value="super-secret",
            description="Test secret",
            tags={"env": "dev", "team": "platform"},
            execution_role_arn="arn:role:override",
        )

        assert response == {"ARN": "arn:secret:test"}
        connector.get_aws_client.assert_called_once_with(
            client_name="secretsmanager",
            execution_role_arn="arn:role:override",
        )
        mock_client.create_secret.assert_called_once()
        assert mock_client.create_secret.call_args.kwargs["Name"] == "/vendors/test"
        assert mock_client.create_secret.call_args.kwargs["SecretString"] == "super-secret"
        assert mock_client.create_secret.call_args.kwargs["Description"] == "Test secret"
        assert mock_client.create_secret.call_args.kwargs["Tags"] == [
            {"Key": "env", "Value": "dev"},
            {"Key": "team", "Value": "platform"},
        ]

    def test_create_secret_requires_name(self, base_connector_kwargs):
        """Ensure create_secret validates required parameters."""
        connector = AWSConnector(**base_connector_kwargs)

        with pytest.raises(ValueError, match="name is required"):
            connector.create_secret(name="", secret_value="value")

    def test_update_secret_calls_aws(self, base_connector_kwargs):
        """Ensure update_secret forwards call to boto3 client."""
        connector = AWSConnector(**base_connector_kwargs)
        mock_client = MagicMock()
        mock_client.update_secret.return_value = {"ARN": "arn:secret:test"}
        connector.get_aws_client = MagicMock(return_value=mock_client)

        response = connector.update_secret(
            secret_id="arn:secret:test",
            secret_value="updated",
            execution_role_arn="arn:role:override",
        )

        assert response == {"ARN": "arn:secret:test"}
        connector.get_aws_client.assert_called_once_with(
            client_name="secretsmanager",
            execution_role_arn="arn:role:override",
        )
        mock_client.update_secret.assert_called_once_with(SecretId="arn:secret:test", SecretString="updated")

    def test_delete_secret_with_recovery_window(self, base_connector_kwargs):
        """Ensure delete_secret honors recovery windows."""
        connector = AWSConnector(**base_connector_kwargs)
        mock_client = MagicMock()
        mock_client.delete_secret.return_value = {"ARN": "arn:secret:test"}
        connector.get_aws_client = MagicMock(return_value=mock_client)

        response = connector.delete_secret(
            secret_id="arn:secret:test",
            recovery_window_days=10,
            execution_role_arn="arn:role:override",
        )

        assert response == {"ARN": "arn:secret:test"}
        mock_client.delete_secret.assert_called_once_with(SecretId="arn:secret:test", RecoveryWindowInDays=10)

    def test_delete_secret_force_delete(self, base_connector_kwargs):
        """Ensure delete_secret can force delete without recovery."""
        connector = AWSConnector(**base_connector_kwargs)
        mock_client = MagicMock()
        mock_client.delete_secret.return_value = {"ARN": "arn:secret:test"}
        connector.get_aws_client = MagicMock(return_value=mock_client)

        connector.delete_secret(secret_id="arn:secret:test", force_delete=True)

        mock_client.delete_secret.assert_called_once_with(
            SecretId="arn:secret:test",
            ForceDeleteWithoutRecovery=True,
        )

    def test_delete_secret_invalid_recovery_window(self, base_connector_kwargs):
        """Ensure invalid recovery window raises error."""
        connector = AWSConnector(**base_connector_kwargs)

        with pytest.raises(ValueError, match="recovery_window_days"):
            connector.delete_secret(secret_id="arn:secret:test", recovery_window_days=60)

    def test_delete_secrets_matching_dry_run(self, base_connector_kwargs):
        """Ensure delete_secrets_matching can run dry without deletions."""
        connector = AWSConnector(**base_connector_kwargs)
        connector.list_secrets = MagicMock(return_value={"secret/a": "arn:a", "secret/b": "arn:b"})
        connector.delete_secret = MagicMock()

        to_delete = connector.delete_secrets_matching(
            name_prefix="/vendors/",
            dry_run=True,
            force_delete=False,
            execution_role_arn="arn:role:override",
        )

        assert to_delete == ["arn:a", "arn:b"]
        connector.delete_secret.assert_not_called()
        connector.list_secrets.assert_called_once_with(
            name_prefix="/vendors/",
            execution_role_arn="arn:role:override",
        )

    def test_delete_secrets_matching_executes_delete(self, base_connector_kwargs):
        """Ensure delete_secrets_matching deletes secrets when not dry run."""
        connector = AWSConnector(**base_connector_kwargs)
        connector.list_secrets = MagicMock(return_value={"secret/a": "arn:a", "secret/b": "arn:b"})
        connector.delete_secret = MagicMock(
            side_effect=[{"ARN": "arn:a"}, {"ARN": "arn:b"}],
        )

        deleted = connector.delete_secrets_matching(
            name_prefix="/vendors/",
            dry_run=False,
            force_delete=True,
            execution_role_arn="arn:role:override",
        )

        assert deleted == ["arn:a", "arn:b"]
        connector.delete_secret.assert_has_calls(
            [
                call(
                    secret_id="arn:a",
                    force_delete=True,
                    recovery_window_days=30,
                    execution_role_arn="arn:role:override",
                ),
                call(
                    secret_id="arn:b",
                    force_delete=True,
                    recovery_window_days=30,
                    execution_role_arn="arn:role:override",
                ),
            ]
        )
