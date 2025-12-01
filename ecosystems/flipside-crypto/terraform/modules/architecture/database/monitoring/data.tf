module "datadog_metadata" {
  source = "git@github.com:FlipsideCrypto/datadog-architecture.git//modules/datadog-metadata"
}

locals {
  datadog_metadata       = lookup(module.datadog_metadata.metadata, local.json_key, {})
  datadog_forwarder_data = lookup(local.datadog_metadata, "forwarder", {})
}

data "aws_cloudwatch_log_group" "rds_os_metrics" {
  count = local.database_infrastructure_data != {} ? 1 : 0

  name = "RDSOSMetrics"
}