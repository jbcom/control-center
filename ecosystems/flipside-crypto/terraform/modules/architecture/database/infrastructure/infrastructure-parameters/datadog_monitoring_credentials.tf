resource "random_password" "database_datadog_monitoring_password" {
  for_each = local.configured_databases

  length  = 24
  special = false
}

resource "aws_ssm_parameter" "database_datadog_monitoring_password" {
  for_each = random_password.database_datadog_monitoring_password

  name        = "/datadog/monitoring/rds/${each.key}"
  description = "Datadog RDS monitoring credentials for ${each.key}"
  type        = "SecureString"
  value = jsonencode({
    dbm      = true
    host     = local.configured_databases[each.key]["endpoint"]
    port     = local.configured_databases[each.key]["db_port"]
    username = "datadog"
    password = each.value.result
    dbname   = local.configured_databases[each.key]["db_name"]
    tags = [
      for k, v in try(local.configured_databases[each.key]["tags"], var.context["tags"]) : "${k}:${v}"
    ]
  })

  overwrite = true

  tags = var.context["tags"]
}

locals {
  datadog_monitoring_parameter_data = {
    databases = {
      for database_name, parameter_data in aws_ssm_parameter.database_datadog_monitoring_password : database_name => {
        datadog_monitoring_credentials = parameter_data["name"]
      }
    }
  }
}