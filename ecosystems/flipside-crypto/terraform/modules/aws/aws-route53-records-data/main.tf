module "aws_route53_records" {
  for_each = toset(var.zone_ids)

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["route53", "list-resource-record-sets", "--hosted-zone-id", each.key]
  aws_cli_query    = "ResourceRecordSets"

  assume_role_arn = var.execution_role_arn
}

locals {
  aws_route53_records_raw_data = {
    for zone_id, results in module.aws_route53_records : zone_id => {
      for record in results["result"] : format("%s_%s", record["Name"], record["Type"]) => {
        for k, v in record :
        replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_") =>
        v
      }
    }
  }

  aws_route53_records_base_data = {
    for zone_id, records_data in local.aws_route53_records_raw_data : zone_id => {
      for record_id, record_data in records_data : record_id => merge({
        for k, v in record_data : k => v if k != "resource_records"
        }, (try(coalesce(record_data["resource_records"]), null) != null ? [
          {
            records = compact([
              for record in record_data["resource_records"] : record["Value"]
            ])
          }
      ] : [])...)
    }
  }

  aws_route53_records_data = {
    for zone_id, records_data in local.aws_route53_records_base_data : zone_id => {
      for record_id, record_data in records_data : record_id => merge({
        for k, v in record_data : k => v if k != "alias_target"
        }, (try(coalesce(record_data["alias_target"]), null) != null ? [
          {
            alias_target = {
              name                   = record_data["alias_target"]["DNSName"]
              zone_id                = record_data["alias_target"]["HostedZoneId"]
              evaluate_target_health = record_data["alias_target"]["EvaluateTargetHealth"]
            }
          }
      ] : [])...)
    }
  }
}