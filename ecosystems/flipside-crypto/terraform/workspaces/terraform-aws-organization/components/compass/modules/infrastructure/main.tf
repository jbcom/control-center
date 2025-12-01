locals {
  tags = merge(var.context["tags"], {
    Copilot = "Copilot"
  })

  environment_name = var.context["environment"]

  kms_key_arn        = var.context["compass_kms_key"]["arn"]
  global_kms_key_arn = var.context["global_kms_key_arn"]

  compass_account = var.context["accounts_by_json_key"]["Compass"]


  json_key            = "Compass"
  ssm_path_prefix     = "/infrastructure/${local.json_key}"
  network_data        = var.context["cluster_networks"][local.json_key]
  vpc_id              = local.network_data["vpc_id"]
  private_subnet_ids  = local.network_data["private_subnet_ids"]
  public_subnet_ids   = local.network_data["public_subnet_ids"]
  allowed_cidr_blocks = local.network_data["allowed_cidr_blocks"]

  compass_assume_role_arn = var.context["compass_assume_role"]["arn"]

  compass_environments = var.context["live_environments"]

  copilot_tags = var.context["copilot_tags"]

  copilot_environment_tags = var.context["copilot_environment_tags"]

  dd_tags = compact([
    for k, v in local.tags : try((lower(k) == lower(v) || v == "" ? lower(k) : "${lower(k)}:${v}"), "")
    if k != "Environment"
  ])
}

resource "aws_codestarconnections_connection" "default" {
  name          = "copilot-compass-Github"
  provider_type = "GitHub"
}

locals {
  base_manifests = [
    {
      environments = {
        for environment_name, environment_secrets in module.environment_secrets :
        environment_name => {
          secrets = {
            for secret_name in environment_secrets.names : basename(secret_name) => secret_name
          }
        }
      }
    },
  ]

  service_manifests_config = var.context["services"]

  records_config = {
    compass_databases = local.compass_db_data
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir
}
