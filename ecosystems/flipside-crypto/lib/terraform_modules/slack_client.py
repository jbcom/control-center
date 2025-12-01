# Shim for Slack client - wraps vendor_connectors.SlackConnector
from vendor_connectors import SlackConnector as SlackClient

__all__ = ["SlackClient"]
