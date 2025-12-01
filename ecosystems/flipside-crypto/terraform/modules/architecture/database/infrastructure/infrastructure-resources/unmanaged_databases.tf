locals {
  unmanaged_databases_file = "${path.root}/secrets/unmanaged_databases.json"
}

data "sops_file" "unmanaged_databases" {
  count = fileexists(local.unmanaged_databases_file) ? 1 : 0

  source_file = local.unmanaged_databases_file
}

locals {
  unmanaged_databases_raw_connection_data  = try(jsondecode(data.sops_file.unmanaged_databases[0].raw), {})
  unmanaged_databases_base_connection_data = try(nonsensitive(local.unmanaged_databases_raw_connection_data), local.unmanaged_databases_raw_connection_data)

  unmanaged_databases_passwords = {
    for database_name, connection_data in local.unmanaged_databases_base_connection_data : database_name => try(connection_data["password"], connection_data)
  }
}

resource "aws_secretsmanager_secret" "password-unmanaged-database" {
  for_each = local.unmanaged_databases_passwords

  name = "/passwords/databases/${each.key}"

  kms_key_id = local.kms_key_arn

  recovery_window_in_days = 0

  force_overwrite_replica_secret = true

  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "password-unmanaged-database" {
  for_each = aws_secretsmanager_secret.password-unmanaged-database

  secret_id     = each.value.id
  secret_string = local.unmanaged_databases_passwords[each.key]
}

resource "aws_secretsmanager_secret_policy" "secret_policy_password-unmanaged-database" {
  for_each = aws_secretsmanager_secret.password-unmanaged-database

  secret_arn = each.value.arn

  policy = local.secret_policy_json
}

module "unmanaged_databases" {
  for_each = local.unmanaged_databases_base_connection_data

  source = "../../database/database-clusters-data"

  rds_cluster_name        = each.key
  rds_cluster_environment = try(each.value["environment"], local.environment)
  rds_cluster_tags = merge(local.tags, {
    Environment = try(each.value["environment"], local.environment)
  }, try(each.value["tags"], {}))

  aws_region           = local.region
  aws_assumed_role_arn = local.execution_role_arn

  tag_cluster = true
}

locals {
  unmanaged_databases = {
    for database_name, database_data in module.unmanaged_databases : database_name => merge(database_data["rds_cluster"], {
      short_name         = lookup(local.unmanaged_databases_base_connection_data[database_name], "short_name", "")
      category           = "databases"
      account_json_key   = local.json_key
      account_id         = local.account_id
      execution_role_arn = local.execution_role_arn
      schema             = try(local.unmanaged_databases_base_connection_data[database_name]["schema"], "public")

      ssm_path_prefix = "${local.ssm_path_prefix}/databases"

      password = aws_secretsmanager_secret.password-unmanaged-database[database_name].id
    })
  }
}

module "unmanaged_database_connection_strings" {
  for_each = local.unmanaged_databases

  source = "../../database/database-connection-strings"

  config = merge(each.value, {
    password = local.unmanaged_databases_passwords[each.key]
  })

  secret_suffix = each.key
  secret_policy = local.secret_policy_json

  tags = local.tags
}

locals {
  configured_unmanaged_databases = {
    for database_name, database_data in local.unmanaged_databases : database_name => merge(database_data, module.unmanaged_database_connection_strings[database_name])
  }
}