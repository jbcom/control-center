"""Vendor Connectors - Universal vendor connectors for the jbcom ecosystem.

This package provides modular connectors for various cloud providers and services:
- AWS: Organizations, SSO/Identity Center, S3, Secrets Manager
- Google Cloud: Workspace, Cloud Platform, Billing, Services (GKE, Compute, etc.)
- GitHub: Repository operations, PR management
- Slack: Channel and message operations
- Vault: HashiCorp Vault secret management
- Zoom: User and meeting management

Usage:
    # Basic connector (session management + secrets)
    from vendor_connectors import AWSConnector
    connector = AWSConnector()

    # Full connector with all operations
    from vendor_connectors.aws import AWSConnectorFull
    connector = AWSConnectorFull()
    accounts = connector.get_accounts()

    # Mixin approach for custom connectors
    from vendor_connectors.aws import AWSConnector, AWSOrganizationsMixin

    class MyConnector(AWSConnector, AWSOrganizationsMixin):
        pass
"""

__version__ = "202511.9.0"

from vendor_connectors.aws import (
    AWSConnector,
    AWSConnectorFull,
    AWSOrganizationsMixin,
    AWSS3Mixin,
    AWSSSOmixin,
)
from vendor_connectors.cloud_params import (
    get_aws_call_params,
    get_cloud_call_params,
    get_google_call_params,
)
from vendor_connectors.connectors import VendorConnectors
from vendor_connectors.github import GithubConnector
from vendor_connectors.google import (
    GoogleBillingMixin,
    GoogleCloudMixin,
    GoogleConnector,
    GoogleConnectorFull,
    GoogleServicesMixin,
    GoogleWorkspaceMixin,
)
from vendor_connectors.slack import SlackConnector
from vendor_connectors.vault import VaultConnector
from vendor_connectors.zoom import ZoomConnector

__all__ = [
    # AWS
    "AWSConnector",
    "AWSConnectorFull",
    "AWSOrganizationsMixin",
    "AWSSSOixin",
    "AWSS3Mixin",
    # Google
    "GoogleConnector",
    "GoogleConnectorFull",
    "GoogleWorkspaceMixin",
    "GoogleCloudMixin",
    "GoogleBillingMixin",
    "GoogleServicesMixin",
    # Other connectors
    "GithubConnector",
    "SlackConnector",
    "VaultConnector",
    "ZoomConnector",
    "VendorConnectors",
    # Cloud param utilities
    "get_cloud_call_params",
    "get_aws_call_params",
    "get_google_call_params",
]
