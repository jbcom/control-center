# Locals
# Instead of hardcoding dummy IDs, we reference actual providers and optionally data sources.
# These locals will correctly pull project/org from the configured Google provider context or data sources.

data "google_organization" "org" {
  domain = "flipsidecrypto.com"
}

locals {
  resolved_google_project_id = data.google_project.current.project_id
  resolved_google_org_id     = data.google_organization.org.name
}

#  Enable Google Cloud APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "run.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "orgpolicy.googleapis.com",
    "sheets.googleapis.com",
    "drive.googleapis.com",
  ])

  project = local.resolved_google_project_id
  service = each.key
}

# Workload Identity Configuration
resource "google_iam_workload_identity_pool" "this" {
  display_name              = "GitHub pool"
  workload_identity_pool_id = "github-pool"
  depends_on                = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "this" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.this.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub CI/CD Pool Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.aud"        = "assertion.aud"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Service Accounts
resource "google_service_account" "github" {
  account_id   = "github"
  display_name = "GitHub Service Account"
  project      = local.resolved_google_project_id
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "hevo" {
  account_id   = "hevo-snowflake"
  display_name = "Hevo Snowflake Service Account"
}

# IAM Role Assignments
resource "google_project_iam_member" "github_owner" {
  project = local.resolved_google_project_id
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.github.email}"
}

# FlipsideCrypto Service Account for SUI GCS cross-account access
resource "google_service_account" "flipsidecrypto_sui" {
  account_id   = "flipsidecrypto-sui-writer"
  display_name = "FlipsideCrypto Service Account for SUI GCS access"
  project      = local.resolved_google_project_id
  depends_on   = [google_project_service.apis]
}

# Grant Storage Object Admin for cross-account bucket write access
resource "google_project_iam_member" "flipsidecrypto_sui_storage_admin" {
  project = local.resolved_google_project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.flipsidecrypto_sui.email}"
}

resource "google_project_iam_member" "hevo_owner" {
  project = local.resolved_google_project_id
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.hevo.email}"
}

# Custom IAM Role
resource "google_project_iam_custom_role" "service_account_manager" {
  role_id = "ServiceAccountMgr"
  title   = "Service Account Manager"
  permissions = [
    "iam.serviceAccounts.create",
    "iam.serviceAccounts.delete",
    "iam.serviceAccounts.get",
    "iam.serviceAccounts.list",
    "iam.serviceAccounts.update",
    "iam.serviceAccountKeys.create",
    "iam.serviceAccountKeys.delete",
    "iam.serviceAccountKeys.get",
    "iam.serviceAccountKeys.list",
    "iam.serviceAccounts.getAccessToken",
    "resourcemanager.projects.getIamPolicy",
    "resourcemanager.projects.setIamPolicy",
  ]
}

# Organization Policy
resource "google_org_policy_policy" "allow_service_account_key_creation" {
  parent = local.resolved_google_org_id

  name = "${local.resolved_google_org_id}/policies/iam.disableServiceAccountKeyCreation"

  spec {
    rules {
      enforce = "FALSE"
    }
  }

  depends_on = [google_project_service.apis]
}

# Service Account Key
resource "google_service_account_key" "hevo" {
  service_account_id = google_service_account.hevo.name

  depends_on = [google_org_policy_policy.allow_service_account_key_creation]
}

module "github-aws-oidc" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-oidc-github"

  context = local.context
}

resource "github_actions_organization_secret" "github-aws-oidc" {
  secret_name     = "AWS_OIDC_ROLE_ARN"
  visibility      = "private"
  plaintext_value = module.github-aws-oidc.arn
}

# resource "snowflake_saml2_integration" "google_sso" {
#   name = "GOOGLE_SSO"
#
#   enabled = true
#
#   saml2_provider  = "CUSTOM"
#   saml2_issuer    = local.snowflake_sso_data["issuer"]
#   saml2_sso_url   = local.snowflake_sso_data["sso_url"]
#   saml2_x509_cert = local.snowflake_sso_data["certificate"]
#
#   saml2_sp_initiated_login_page_label = "GOOGLE_SSO"
#   saml2_enable_sp_initiated           = true
# }

resource "aws_iam_saml_provider" "googleworkspace" {
  name                   = "GoogleWorkspace"
  saml_metadata_document = local.googleworkspace_idp_data

  tags = merge(local.context["tags"], {
    Name = "GoogleWorkspace"
  })
}

module "googleworkspace_sso_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-saml"
  version = "5.37.1"

  create_role = true

  role_name = "GoogleWorkspaceSSO"

  tags = merge(local.context["tags"], {
    Name = "GoogleWorkspace"
  })

  provider_id = aws_iam_saml_provider.googleworkspace.id

  role_policy_arns = [
    "arn:aws:iam::aws:policy/AdministratorAccess",
  ]

  number_of_role_policy_arns = 1
}

locals {
  records_config = merge({
    github                                   = module.github-aws-oidc,
    flipsidecrypto_sui_service_account_email = google_service_account.flipsidecrypto_sui.email,
    hevo_postgres = {
      readonly_user = {
        username    = module.hevo_readonly_user.username,
        secret_name = module.hevo_readonly_user.secret_name,
        secret_arn  = module.hevo_readonly_user.secret_arn,
        database    = module.hevo_readonly_user.database,
        schema      = module.hevo_readonly_user.schema,
        host        = "product-eng-velocity-mark-2.cik7nbaqdhks.us-east-1.rds.amazonaws.com",
        port        = 5432
      }
    }
  })
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspace_dir}"

  log_file_name = "permanent_record.log"
}
