"""Tests for AWSConnector."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from cloud_connectors.aws import AWSConnector


class TestAWSConnector:
    """Test suite for AWSConnector."""

    def test_init_without_role(self, base_connector_kwargs):
        """Test initialization without execution role."""
        connector = AWSConnector(**base_connector_kwargs)
        assert connector.execution_role_arn is None
        assert connector.aws_sessions == {}
        assert connector.aws_clients == {}
        assert connector.default_aws_session is not None

    def test_init_with_role(self, base_connector_kwargs):
        """Test initialization with execution role."""
        role_arn = "arn:aws:iam::123456789012:role/TestRole"
        connector = AWSConnector(execution_role_arn=role_arn, **base_connector_kwargs)
        assert connector.execution_role_arn == role_arn

    @patch("cloud_connectors.aws.boto3.Session")
    def test_assume_role_success(self, mock_session_class, base_connector_kwargs):
        """Test successful role assumption."""
        # Setup mocks
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

    @patch("cloud_connectors.aws.boto3.Session")
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

    @patch("cloud_connectors.aws.boto3.Session")
    def test_create_standard_retry_config(self, mock_session_class, base_connector_kwargs):
        """Test creating standard retry configuration."""
        config = AWSConnector.create_standard_retry_config(max_attempts=5)
        assert config.retries["max_attempts"] == 5
        assert config.retries["mode"] == "standard"

    @patch("cloud_connectors.aws.boto3.Session")
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

    @patch("cloud_connectors.aws.boto3.Session")
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
