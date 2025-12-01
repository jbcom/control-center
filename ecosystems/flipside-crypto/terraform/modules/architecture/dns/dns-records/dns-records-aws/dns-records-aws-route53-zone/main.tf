locals {
  zone_id = var.zone_data["zone_id"]

  child_zones_data = {
    for json_key, infrastructure_data in var.infrastructure : json_key => {
      for zone_name, zone_data in lookup(infrastructure_data, "zones", {}) : zone_name => zone_data if zone_data["parent_zone_name"] == var.zone_name
    }
  }

  zone_certificates_data = {
    for json_key, infrastructure_data in var.infrastructure : json_key => {
      for certificate_name, certificate_data in lookup(infrastructure_data, "certificates", {}) : certificate_name => certificate_data if certificate_data["zone_name"] == var.zone_name || certificate_data["zone_id"] == local.zone_id
    }
  }
}

resource "aws_route53domains_registered_domain" "domain_registration" {
  count = var.zone_data["parent_zone_id"] == "" && var.zone_data["parent_zone_name"] == "" && !var.zone_data["externally_registered_zone"] ? 1 : 0

  domain_name = var.zone_name

  dynamic "name_server" {
    for_each = toset(sort(var.zone_data["zone_name_servers"]))

    content {
      name = name_server.key
    }
  }
}

moved {
  from = aws_route53domains_registered_domain.domain_registration
  to   = aws_route53domains_registered_domain.domain_registration[0]
}

module "child_zones" {
  for_each = local.child_zones_data

  source = "./dns-records-aws-route53-zone-children"

  parent_zone_id = local.zone_id

  children = each.value
}

locals {
  redirects_data = lookup(var.zone_data, "redirects", {})
}

module "cloudfront-redirect" {
  providers = {
    aws            = aws
    aws.cloudfront = aws.cloudfront
  }

  for_each = local.redirects_data

  source = "../../../../../cloudfront/cloudfront-redirect"

  name                = "${each.key}.${var.zone_name}"
  redirect_target     = each.value["to"]
  acm_certificate_arn = each.value["acm_certificate_arn"]

  context = var.context
}

resource "aws_route53_record" "redirect" {
  for_each = module.cloudfront-redirect

  zone_id = local.zone_id
  name    = "${each.key}.${var.zone_name}"
  type    = "A"

  alias {
    name                   = each.value.domain_name
    zone_id                = each.value.hosted_zone_id
    evaluate_target_health = true
  }

  allow_overwrite = true
}