locals {
  secret_files = toset(formatlist("%s/%s/%s", var.rel_to_root, var.secrets_dir, var.config.files))
}

data "sops_file" "secret_data" {
  for_each = local.secret_files

  source_file = each.key
}

module "secret_infrastructure_asset_data" {
  for_each = var.config.infrastructure

  source = "../../../../infrastructure/infrastructure-metadata"

  category_name = each.value.category

  matchers = each.value.matchers

  account_map = each.value.accounts

  data_key = each.value.key

  context = var.context
}

module "secret_architecture_asset_data" {
  for_each = var.config.architecture

  source = "../../../../secrets/secrets-metadata"

  category_name = each.value.category

  asset_name = each.value.key

  account_map = each.value.accounts

  context = var.context
}

locals {
  secret_query_data = merge({
    for secret_key, asset_data in module.secret_infrastructure_asset_data : secret_key => {
      id   = asset_data.asset
      type = var.config.infrastructure[secret_key].type
    }
    }, {
    for secret_key, asset_data in module.secret_architecture_asset_data : secret_key => {
      id   = asset_data["asset"]
      type = "secretsmanager"
    }
    }, {
    for secret_key, secret_id in var.config.secrets : secret_key => {
      id   = secret_id
      type = "secretsmanager"
    }
    }, {
    for secret_key, secret_id in var.config.parameters : secret_key => {
      id   = secret_id
      type = "ssm"
    }
    }, flatten([
      for ssm_path_prefix, secrets_config in var.config.parameters_by_path : [
        for secret_key, secret_id in secrets_config : {
          (secret_key) = {
            id   = secret_id
            type = "ssm"
            path = "/${trimprefix(ssm_path_prefix, "/")}"
          }
        }
      ]
  ])...)
}

resource "local_sensitive_file" "debug" {
  count = var.debug_file != "" ? 1 : 0

  filename = "${path.cwd}/query-${var.debug_file}"

  content = jsonencode(local.secret_query_data)
}

module "secrets_data" {
  source = "./secrets-data-from-aws"

  secrets = local.secret_query_data
}

locals {
  secrets_data = merge(module.secrets_data.secrets, var.config.data, flatten([
    for _, file_data in data.sops_file.secret_data : [
      for k, v in try(yamldecode(file_data["raw"]), jsondecode(file_data["raw"]), {}) : {
        (k) = v
      }
    ]
  ])...)
}
