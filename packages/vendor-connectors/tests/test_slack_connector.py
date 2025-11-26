"""Tests for SlackConnector."""

from unittest.mock import MagicMock, patch

from vendor_connectors.slack import SlackConnector


class TestSlackConnector:
    """Test suite for SlackConnector."""

    @patch("vendor_connectors.slack.WebClient")
    def test_init(self, mock_webclient_class, base_connector_kwargs):
        """Test initialization."""
        mock_client = MagicMock()
        mock_webclient_class.return_value = mock_client

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        assert connector.web_client is not None
        assert connector.bot_web_client is not None

    @patch("vendor_connectors.slack.WebClient")
    def test_get_bot_channels(self, mock_webclient_class, base_connector_kwargs):
        """Test getting bot channels."""
        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {
            "channels": [{"name": "general", "id": "C12345"}, {"name": "random", "id": "C67890"}]
        }

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        channels = connector.get_bot_channels()
        assert "general" in channels
        assert channels["general"]["id"] == "C12345"

    @patch("vendor_connectors.slack.WebClient")
    def test_send_message(self, mock_webclient_class, base_connector_kwargs):
        """Test sending a message."""
        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {"channels": [{"name": "general", "id": "C12345"}]}
        mock_bot_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        ts = connector.send_message(channel_name="general", text="Test message", blocks=[])

        assert ts == "1234567890.123456"
        mock_bot_client.chat_postMessage.assert_called_once()
