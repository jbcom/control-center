"""Google connector constants aligned with terraform-modules settings.

These constants provide default configurations for Google Cloud and Workspace
operations that match the terraform-modules library's established patterns.
"""

from __future__ import annotations

DEFAULT_DOMAIN = "flipsidecrypto.com"

# Full OAuth scopes matching terraform-modules for maximum compatibility
DEFAULT_SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/apps.alerts",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/cloud-identity",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.activity",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.userschema",
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/admin.directory.orgunit",
    "https://www.googleapis.com/auth/apps.groups.settings",
    "https://www.googleapis.com/auth/apps.licensing",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-billing",
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/iam",
    "https://www.googleapis.com/auth/compute",
    "https://www.googleapis.com/auth/cloudkms",
    "https://www.googleapis.com/auth/logging.admin",
    "https://www.googleapis.com/auth/monitoring",
    "https://www.googleapis.com/auth/sqlservice.admin",
    "https://www.googleapis.com/auth/devstorage.full_control",
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/service.management",
]

# GCP Security Project defaults
GCP_SECURITY_PROJECT = {
    "id": "flipside-security-admin",
    "name": "Security Administration",
    "resource_labels": {
        "managed-by": "terraform",
        "environment": "global",
        "team": "security",
    },
}

# KMS configuration for terraform secrets
GCP_KMS = {
    "keyring_name": "terraform-secrets",
    "key_name": "terraform-key",
    "key_rotation_period": "7776000s",  # 90 days
}

# Required IAM roles for organization-level operations
GCP_REQUIRED_ORGANIZATION_ROLES = [
    "roles/owner",
    "roles/resourcemanager.projectIamAdmin",
    "roles/serviceusage.serviceUsageAdmin",
]

# Required IAM roles for project-level operations
GCP_REQUIRED_ROLES = GCP_REQUIRED_ORGANIZATION_ROLES + [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/storage.admin",
]

# Required APIs for standard GCP operations
GCP_REQUIRED_APIS = [
    "bigquery.googleapis.com",
    "cloudbilling.googleapis.com",
    "cloudidentity.googleapis.com",
    "cloudassets.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "orgpolicy.googleapis.com",
    "pubsub.googleapis.com",
    "serviceusage.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
]

# Default OUs for user filtering
DEFAULT_USER_OUS = ["/Users", "Users/2FANotEnforced", "/Contract"]

__all__ = [
    "DEFAULT_DOMAIN",
    "DEFAULT_SCOPES",
    "GCP_SECURITY_PROJECT",
    "GCP_KMS",
    "GCP_REQUIRED_APIS",
    "GCP_REQUIRED_ORGANIZATION_ROLES",
    "GCP_REQUIRED_ROLES",
    "DEFAULT_USER_OUS",
]
