locals {
  account_infrastructure_data = var.infrastructure[var.json_key]
  zones_data                  = local.account_infrastructure_data["zones"]
}

module "default" {
  providers = {
    aws            = aws
    aws.cloudfront = aws.cloudfront
  }

  for_each = local.zones_data

  source = "./dns-records-aws-route53-zone"

  zone_name = each.key
  zone_data = each.value

  infrastructure = var.infrastructure

  context = var.context
}