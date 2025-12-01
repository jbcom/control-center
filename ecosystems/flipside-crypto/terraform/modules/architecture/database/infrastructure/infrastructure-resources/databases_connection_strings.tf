module "database_connection_strings" {
  for_each = local.configured_databases

  source = "../../database/database-connection-strings"

  config = merge(each.value, {
    password = local.configured_databases_passwords[each.value["short_name"]]
  })

  secret_suffix = each.key
  secret_policy = local.secret_policy_json

  kms_key_arn = local.secrets_kms_key_arn

  tags = local.tags
}

locals {
  configured_database_connection_strings = {
    databases = {
      for database_name, database_data in module.database_connection_strings : database_name => database_data
    }
  }
}