data "assert_test" "databases_assets_contain_dsn" {
  for_each = local.configured_databases

  test = contains(keys(each.value), "dsn")

  throw = "databases/${each.key} does not have DSN Secrets Manager ID:\n${yamlencode(each.value)}"
}

data "aws_secretsmanager_secret_version" "database_dsns" {
  for_each = local.configured_databases

  secret_id = each.value["dsn"]
}

locals {
  configured_database_dsns = {
    for asset_name, secret_data in data.aws_secretsmanager_secret_version.database_dsns : asset_name => secret_data["secret_string"]
  }
}

data "assert_test" "databases_assets_contain_url" {
  for_each = local.configured_databases

  test = contains(keys(each.value), "url")

  throw = "databases/${each.key} does not have URL Secrets Manager ID:\n${yamlencode(each.value)}"
}

data "aws_secretsmanager_secret_version" "database_urls" {
  for_each = local.configured_databases

  secret_id = each.value["url"]
}

locals {
  configured_database_urls = {
    for asset_name, secret_data in data.aws_secretsmanager_secret_version.database_urls : asset_name => secret_data["secret_string"]
  }
}

module "database_connection_string_ssm_parameters" {
  providers = {
    aws = aws.parameters_store
  }

  source = "./infrastructure-parameters-store"

  infrastructure = {
    for asset_name, asset_data in local.configured_databases : asset_name => merge(asset_data, {
      dsn = local.configured_database_dsns[asset_name]
      url = local.configured_database_urls[asset_name]
    })
  }

  allowlist = [
    "dsn",
    "url",
  ]

  transparent_ssm_path_prefix = "/root"

  context = var.context
}

locals {
  configured_database_connection_string_ssm_parameters = {
    databases = {
      for asset_name, asset_parameters_data in module.database_connection_string_ssm_parameters.ssm_parameters : asset_name => {
        ssm_parameters = asset_parameters_data
      }
    }
  }
}
