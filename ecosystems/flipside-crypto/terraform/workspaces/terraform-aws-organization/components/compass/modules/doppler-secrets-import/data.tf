data "doppler_secrets" "gitops" {
  project = "gitops"
  config  = "ci_vendors"
}

data "aws_secretsmanager_secret" "compass_rds_database_url" {
  name = "/connection-strings/databases/compass-us-east-1-compass-${var.environment_name}-public/url"
}

data "aws_secretsmanager_secret_version" "compass_rds_database_url" {
  secret_id = data.aws_secretsmanager_secret.compass_rds_database_url.id
}

data "sops_file" "compass_global_secrets" {
  source_file = "${var.rel_to_root}/secrets/compass.json"
}

data "sops_file" "compass_environment_secrets" {
  source_file = "${var.rel_to_root}/secrets/compass-${var.environment_name}.json"
}

locals {
  env_vars_config = var.context["environment_variables"]

  vendors_map = {
    CA_KEY          = "temporal_key"
    CA_PEM          = "temporal_pem"
    DD_API_KEY      = "datadog_api_key"
    DD_APP_KEY      = "datadog_app_key"
    DATADOG_API_KEY = "datadog_app_key"
  }

  compass_environment_secrets = nonsensitive(merge({
    for k, v in local.env_vars_config : k => v if k != "environments"
    }, local.env_vars_config["environments"][var.environment_name], jsondecode(data.sops_file.compass_global_secrets.raw),
    jsondecode(data.sops_file.compass_environment_secrets.raw), {
      DATABASE_URL = data.aws_secretsmanager_secret_version.compass_rds_database_url.secret_string
      }, {
      for k, v in local.vendors_map : k => var.vendors[v]
  }))
}
