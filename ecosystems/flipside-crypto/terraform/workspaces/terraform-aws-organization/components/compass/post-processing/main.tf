module "domain" {
  for_each = toset(local.context["live_environments"])

  source = "../modules/domain"

  environment_name = each.key

  context = local.context
}

module "datadog_lambda_forwarder" {
  source  = "cloudposse/datadog-lambda-forwarder/aws"
  version = "1.7.0"

  name       = "datadog"
  attributes = ["forwarder"]

  forwarder_rds_enabled = true
  forwarder_log_enabled = true
  cloudwatch_forwarder_log_groups = merge({
    for environment_name, database_data in local.context["compass_databases"] : environment_name => {
      name           = format("/aws/rds/cluster/%s/postgresql", database_data["db_cluster_identifier"])
      filter_pattern = ""
    }
    }, {
    for log_group_name in data.aws_cloudwatch_log_groups.codebuild.log_group_names :
    basename(log_group_name) => {
      name           = log_group_name
      filter_pattern = ""
    }
  })

  dd_api_key_source = {
    resource   = "ssm"
    identifier = local.context["datadog_api_key_ssm_path"]
  }

  context = local.context
}
