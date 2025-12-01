import os
from http import HTTPStatus
from logging import DEBUG as _DEFAULT_LOG_LEVEL
from os import getenv

GITHUB_REPO = "terraform-modules"
GITHUB_OWNER = "FlipsideCrypto"


# ----------------------
# CI Environment Detection
# ----------------------


def is_ci_environment() -> bool:
    """Detect if running in a CI environment."""
    return any(
        [
            getenv("CI"),
            getenv("GITHUB_ACTIONS"),
            getenv("GITLAB_CI"),
            getenv("CIRCLECI"),
            getenv("JENKINS_URL"),
            getenv("BUILDKITE"),
            getenv("TRAVIS"),
        ]
    )


def is_github_actions() -> bool:
    """Detect if running specifically in GitHub Actions."""
    return bool(getenv("GITHUB_ACTIONS"))


def get_github_env_file() -> str | None:
    """Get the GITHUB_ENV file path if available."""
    return getenv("GITHUB_ENV")


def get_github_output_file() -> str | None:
    """Get the GITHUB_OUTPUT file path if available."""
    return getenv("GITHUB_OUTPUT")


# CI detection flags (evaluated at import time for efficiency)
CI_ENVIRONMENT = is_ci_environment()
GITHUB_ACTIONS_ENVIRONMENT = is_github_actions()
GITHUB_ENV_FILE = get_github_env_file()
GITHUB_OUTPUT_FILE = get_github_output_file()

FLASK_PORT = getenv("PORT", 8080)

INFO = 0
WARNING = 1
ERROR = 2
OK = HTTPStatus.OK
BAD_REQUEST = HTTPStatus.BAD_REQUEST
UNAUTHORIZED = HTTPStatus.UNAUTHORIZED

DEFAULT_LOG_LEVEL = _DEFAULT_LOG_LEVEL

IDENTIFIER_REGEX = r"\W|\s"
TITLE_REGEX = r"\W|[_-)|\s"

BLUEPRINTS_BACKUP_DIR = "records/blueprints"
BLUEPRINTS_TABLE_NAME = "blueprints"
ENTITIES_BACKUP_DIR = "records/entities"
ENTITIES_DELETION_WINDOW = 90

INTERNAL_TOOLING_CLUSTER_NAME = "internal-tooling-assets"

GITOPS_REPO_BRANCH_PREFIX = "terraform-modules"
GITOPS_REPO_BRANCH_DELIM = "/"
GITOPS_METADATA_PROPERTY = "gitops_metadata"

MAX_FILE_LOCK_WAIT = 600
MAX_PROC_RUN_TIME = 30

TERRAFORM_MODULES_DIR = "."
TERRAFORM_MODULES_BINARY_NAME = "tm_cli"
TERRAFORM_MODULES_NAME_DELIM = "-"

METADATA_RECORDS_DIR = "records/metadata"

VERBOSE = False
VERBOSITY = 1
DRY_RUN = False

LOG_FILE_NAME = "run.log"

SAVE_EVENTS_TO_GITHUB = True

MAX_DESCRIPTION_LENGTH = 200

LOG_API_REQUESTS = getenv("LOG_API_REQUESTS", False)

IDENTIFIER_DOMAIN = "flipsidecrypto.com"

SCOPES = [
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
    "https://www.googleapis.com/auth/cloud-platform",  # Broad access to all GCP resources
    "https://www.googleapis.com/auth/cloud-billing",  # Billing accounts management
    "https://www.googleapis.com/auth/bigquery",  # BigQuery datasets
    "https://www.googleapis.com/auth/iam",  # IAM roles and service accounts
    "https://www.googleapis.com/auth/compute",  # Compute Engine
    "https://www.googleapis.com/auth/cloudkms",  # Key Management Service (KMS)
    "https://www.googleapis.com/auth/logging.admin",  # Stackdriver logging
    "https://www.googleapis.com/auth/monitoring",  # Stackdriver monitoring
    "https://www.googleapis.com/auth/sqlservice.admin",  # Cloud SQL
    "https://www.googleapis.com/auth/devstorage.full_control",  # Full access to Cloud Storage
    "https://www.googleapis.com/auth/pubsub",  # Pub/Sub service
    "https://www.googleapis.com/auth/service.management",  # Service management APIs
]

SUBJECT = "internal-tooling-bot@flipsidecrypto.com"

DEFAULT_USER_OUS = ["/Users", "Users/2FANotEnforced", "/Contract"]

# ----------------------
# GCP Configuration
# ----------------------

# Core GCP Configuration
GCP_DOMAIN = "flipsidecrypto.com"
GCP_SECURITY_PROJECT = {
    "id": "flipside-security-admin",
    "name": "Security Administration",
    "resource_labels": {
        "managed-by": "terraform",
        "environment": "global",
        "team": "security",
    },
}

# Service Account Configuration
GCP_SERVICE_ACCOUNT = {
    "name": "terraform-org-admin",
    "display_name": "Terraform Organization Admin",
    "description": "Service account for Terraform organization management",
}

# KMS Configuration
GCP_KMS = {
    "keyring_name": "terraform-secrets",
    "key_name": "terraform-key",
    "key_rotation_period": "7776000s",  # 90 days
}

# Billing Configuration
GCP_BILLING = {
    "account_name": "DevOps Subscriptions",
}

# Region and User Type
GCP_REGION = "us-east1"
GCP_USER_TYPE = "user"

# APIs and IAM Roles
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
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
]

GCP_REQUIRED_ORGANIZATION_ROLES = [
    "roles/owner",
    "roles/resourcemanager.projectIamAdmin",
    "roles/serviceusage.serviceUsageAdmin",
]

GCP_REQUIRED_ROLES = GCP_REQUIRED_ORGANIZATION_ROLES + [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/storage.admin",
    "roles/bigquery.admin",
    "roles/compute.admin",
    "roles/container.admin",
]

GCP_BOOLEAN_CONSTRAINTS = {
    "constraints/storage.publicAccessPrevention": True,
    "constraints/storage.uniformBucketLevelAccess": True,
    "constraints/compute.requireOsLogin": True,
    "constraints/iam.automaticIamGrantsForDefaultServiceAccounts": True,
    "constraints/iam.disableServiceAccountKeyCreation": False,
    "constraints/iam.disableServiceAccountKeyUpload": False,
    "constraints/compute.disableNestedVirtualization": True,
    "constraints/compute.disableSerialPortAccess": True,
    "constraints/sql.restrictAuthorizedNetworks": True,
    "constraints/sql.restrictPublicIp": True,
    "constraints/compute.restrictXpnProjectLienRemoval": True,
    "constraints/compute.setNewProjectDefaultToZonalDNSOnly": True,
    "constraints/compute.skipDefaultNetworkCreation": True,
    "constraints/compute.disableVpcExternalIpv6": True,
}

GCP_LIST_CONSTRAINTS = {
    "constraints/essentialcontacts.allowedContactDomains": {"enforced": False},
    "constraints/iam.allowedPolicyMemberDomains": {"enforced": False},
    "constraints/serviceuser.services": {"enforced": False},
    "constraints/compute.vmExternalIpAccess": {"enforced": True},
    "constraints/compute.restrictProtocolForwardingCreationForTypes": {"allowedValues": ["INTERNAL"]},
}

# ----------------------
# Other General Configuration
# ----------------------

# Retry Logic
RETRY_SETTINGS = {
    "max_retries": 3,
    "retry_delay": 5,  # seconds
}

# Timeouts
TIMEOUTS = {
    "read_timeout": 300,  # 5 minutes
}
