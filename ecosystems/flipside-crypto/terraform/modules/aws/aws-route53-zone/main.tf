data "aws_region" "current" {}

resource "aws_route53_zone" "this" {
  name = var.config.name

  comment = var.config.comment

  delegation_set_id = var.config.delegation_set_id

  force_destroy = var.config.force_destroy

  tags = var.config.tags

  dynamic "vpc" {
    for_each = {
      for idx, vpc_config in var.config.vpcs : format("%s#%s", idx, vpc_config["vpc_id"]) => vpc_config
      if try(coalesce(vpc_config["vpc_id"]), null) != null
    }

    content {
      vpc_id     = vpc.value["vpc_id"]
      vpc_region = try(coalesce(vpc.value["vpc_region"]), data.aws_region.current.name)
    }
  }
}