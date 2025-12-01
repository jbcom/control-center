resource "doppler_project" "gitops" {
  name        = "gitops"
  description = "The Internal Tooling Gitops project"
}

resource "doppler_environment" "ci" {
  project = doppler_project.gitops.name
  slug    = "ci"
  name    = "Continuous Integration"
}

resource "doppler_config" "ci_vendors" {
  project     = doppler_project.gitops.name
  environment = doppler_environment.ci.slug
  name        = "ci_vendors"
}

locals {
  string_secrets = {
    for k, v in local.vendors_data : k => v if try(merge(v, {}), null) == null
  }

  map_secrets = {
    for k, v in local.vendors_data : k => v if try(merge(v, {}), null) != null
  }
}

resource "doppler_secret" "vendor" {
  for_each = nonsensitive(local.vendors_data)

  project    = doppler_project.gitops.name
  config     = doppler_config.ci_vendors.name
  name       = each.key == "flyio_token" ? "FLYIO_BOT_TOKEN" : (startswith(each.key, "github") ? upper("FLIPSIDE_${each.key}") : upper(each.key))
  value      = try(local.string_secrets[each.key], jsonencode(local.map_secrets[each.key]))
  visibility = "restricted"
}

data "sops_file" "quay_credentials" {
  source_file = "${local.rel_to_root}/secrets/quay-credentials.yaml"

  input_type = "yaml"
}

locals {
  quay_credentials_data = yamldecode(data.sops_file.quay_credentials.raw)
}

resource "doppler_secret" "quay_credentials" {
  for_each = try(nonsensitive(local.quay_credentials_data), local.quay_credentials_data)

  project    = doppler_project.gitops.name
  config     = doppler_config.ci_vendors.name
  name       = upper(each.key)
  value      = each.value
  visibility = "restricted"
}

resource "doppler_secret" "quay_robot_token" {
  project    = doppler_project.gitops.name
  config     = doppler_config.ci_vendors.name
  name       = "QUAY_ROBOT_TOKEN"
  value      = local.quay_credentials_data["quay_password"]
  visibility = "restricted"
}

resource "doppler_secrets_sync_github_actions" "backend_prod" {
  integration = "c770b66d-927d-4cc4-a270-9f1d47fd103c"
  project     = doppler_project.gitops.name
  config      = doppler_config.ci_vendors.name

  sync_target = "org"
  org_scope   = "private"
}

resource "aws_secretsmanager_secret" "vendors" {
  name = "/vendors"

  tags = merge(local.context["tags"], {
    Name = "/vendors"
  })
}

resource "aws_secretsmanager_secret_version" "vendors" {
  secret_id     = aws_secretsmanager_secret.vendors.id
  secret_string = jsonencode(local.vendors_data)
}

data "sops_file" "hevo_google_sa_credentials" {
  source_file = "${local.rel_to_root}/secrets/hevo-google-sa.json"

  input_type = "json"
}

resource "doppler_environment" "bi" {
  project = doppler_project.gitops.name
  slug    = "bi"
  name    = "Business Intelligence"
}

resource "doppler_config" "bi_analytics" {
  project     = doppler_project.gitops.name
  environment = doppler_environment.bi.slug
  name        = "bi_analytics"
}

resource "doppler_secret" "hevo_google_sa_credentials" {
  project = doppler_project.gitops.name
  config  = doppler_config.bi_analytics.name
  name    = "HEVO_SNOWFLAKE_GOOGLE_SA"
  value   = data.sops_file.hevo_google_sa_credentials.raw
}

locals {
  records_config = {
    doppler = {
      project     = doppler_project.gitops
      environment = doppler_environment.ci
      config      = doppler_config.ci_vendors
      integration = doppler_secrets_sync_github_actions.backend_prod
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspace_dir}"

  log_file_name = "permanent_record.log"
}
