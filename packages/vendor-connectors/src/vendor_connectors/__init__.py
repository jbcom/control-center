"""Vendor Connectors - Universal vendor connectors for the jbcom ecosystem."""

__version__ = "202511.6.2"

from vendor_connectors.aws import AWSConnector
from vendor_connectors.connectors import VendorConnectors
from vendor_connectors.github import GithubConnector
from vendor_connectors.google import GoogleConnector
from vendor_connectors.slack import SlackConnector
from vendor_connectors.vault import VaultConnector
from vendor_connectors.zoom import ZoomConnector

__all__ = [
    "AWSConnector",
    "GithubConnector",
    "GoogleConnector",
    "SlackConnector",
    "VaultConnector",
    "ZoomConnector",
    "VendorConnectors",
]
