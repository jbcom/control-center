locals {
  account_data = var.context["account"]
  json_key     = local.account_data["json_key"]

  database_infrastructure_data = lookup(var.infrastructure, "databases", {})
}

data "aws_secretsmanager_secret_version" "database_url" {
  for_each = local.database_infrastructure_data

  secret_id = each.value["url"]
}

data "aws_ssm_parameter" "datadog_monitoring_credentials" {
  for_each = local.database_infrastructure_data

  name = each.value["datadog_monitoring_credentials"]
}

locals {
  datadog_monitoring_credentials_data = {
    for database_name, parameter_data in data.aws_ssm_parameter.datadog_monitoring_credentials : database_name => jsondecode(parameter_data["value"])
  }

  refresh = false
}

module "datadog_integration" {
  source = "git@github.com:FlipsideCrypto/datadog-architecture.git//modules/datadog-integration"

  name = "postgres"

  instances = values(local.datadog_monitoring_credentials_data)
}

resource "null_resource" "sql_injection" {
  for_each = local.datadog_monitoring_credentials_data

  triggers = {
    password = nonsensitive(each.value["password"])
    url      = nonsensitive(split("?", data.aws_secretsmanager_secret_version.database_url[each.key].secret_string)[0])
    refresh  = local.refresh ? timestamp() : ""
    checksum = filesha256("${path.module}/queries/monitoring.sql")
  }

  provisioner "local-exec" {
    command = <<-EOF
      docker run --rm --name psql-injection-${each.key} -w "$WORK_DIR" -v "$${WORK_DIR}:$${WORK_DIR}" postgres psql "${self.triggers.url}" --no-psqlrc --single-transaction --pset=pager=off --set=ON_ERROR_STOP=1 --echo-all --set=userPassword="${self.triggers.password}" -f "$${WORK_DIR}/queries/monitoring.sql"
    EOF

    environment = {
      WORK_DIR = abspath(path.module)
    }

    interpreter = ["bash", "-c"]
  }
}

resource "aws_lambda_permission" "cloudwatch_enhanced_rds_monitoring" {
  count = local.database_infrastructure_data != {} && local.datadog_forwarder_data != {} ? 1 : 0

  statement_id  = "datadog-forwarder-rds-cloudwatch-logs-permission"
  action        = "lambda:InvokeFunction"
  function_name = local.datadog_forwarder_data["forwarder_name"]
  principal     = "logs.amazonaws.com"
  source_arn    = format("%s:*", join("", data.aws_cloudwatch_log_group.rds_os_metrics.*.arn))
}

resource "aws_cloudwatch_log_subscription_filter" "datadog_log_subscription_filter_rds" {
  count = local.database_infrastructure_data != {} && local.datadog_forwarder_data != {} ? 1 : 0

  name            = "datadog-forwarder-rds-cloudwatch-logs"
  log_group_name  = join("", data.aws_cloudwatch_log_group.rds_os_metrics.*.name)
  destination_arn = local.datadog_forwarder_data["forwarder_arn"]
  filter_pattern  = ""

  depends_on = [
    aws_lambda_permission.cloudwatch_enhanced_rds_monitoring,
  ]
}