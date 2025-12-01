module "aws_route53_zones" {
  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["route53", "list-hosted-zones", "--no-paginate"]
  aws_cli_query    = "HostedZones"

  assume_role_arn = var.execution_role_arn
}

module "aws_route53_zone_data" {
  for_each = toset([
    for result in module.aws_route53_zones.result : trimprefix(result["Id"], "/hostedzone/")
  ])

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["route53", "get-hosted-zone", "--id", each.key]

  assume_role_arn = var.execution_role_arn
}

module "aws_route53_zone_tag_data" {
  for_each = module.aws_route53_zone_data

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["route53", "list-tags-for-resources", "--resource-type", "hostedzone", "--resource-ids", each.key]
  aws_cli_query    = "ResourceTagSets"

  assume_role_arn = var.execution_role_arn
}

locals {
  aws_route53_zone_tags_raw_data = {
    for zone_id, tags_data in module.aws_route53_zone_tag_data : zone_id => {
      for resource in tags_data["result"] : resource["ResourceId"] => {
        for tag in resource["Tags"] : tag["Key"] => tag["Value"]
      }
    }
  }

  aws_route53_zone_tags_data = {
    for zone_id, zones in local.aws_route53_zone_tags_raw_data : zone_id => try(zones[zone_id], {})
  }

  aws_route53_zone_raw_data = {
    for zone_id, results in module.aws_route53_zone_data : zone_id => merge({
      for k, v in results["result"] : replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_") => v
      }, {
      zone_id = zone_id
      tags    = local.aws_route53_zone_tags_data[zone_id]
    })
  }

  aws_route53_zone_base_data = {
    for zone_id, zone_data in local.aws_route53_zone_raw_data : zone_id => merge({
      for k, v in zone_data : k => v if k != "hosted_zone"
      }, {
      for k, v in zone_data["hosted_zone"] : replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_") => v
    })
  }

  aws_route53_zone_data = {
    for zone_id, zone_data in local.aws_route53_zone_base_data : zone_id => merge({
      for k, v in zone_data : k => v if k != "config"
      }, {
      for k, v in zone_data["config"] : replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_") => v
    })
  }
}
