# Data Sources
data "google_project" "current" {}

data "google_organization" "current" {
  domain = "flipsidecrypto.com"
}

# Local Variables
locals {
  google_project_id = data.google_project.current.project_id
  google_org_id     = "organizations/${data.google_organization.current.org_id}"
}

data "sops_file" "credentials" {
  source_file = "${path.module}/${local.workspace_secrets_dir}/credentials.yaml"
}

locals {
  credentials_data = yamldecode(data.sops_file.credentials.raw)
}

data "sops_file" "googleworkspace_idp" {
  source_file = "${path.module}/${local.workspace_secrets_dir}/GoogleIDPMetadata.xml"

  input_type = "raw"
}

locals {
  googleworkspace_idp_data = data.sops_file.googleworkspace_idp.raw
}

data "sops_file" "snowflake-saml" {
  source_file = "${path.module}/${local.workspace_secrets_dir}/snowflake_saml.json"
}

locals {
  snowflake_sso_data = jsondecode(data.sops_file.snowflake-saml.raw)
}
