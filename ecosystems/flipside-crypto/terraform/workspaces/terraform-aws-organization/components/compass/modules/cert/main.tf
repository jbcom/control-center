terraform {
  required_providers {
    cloudflare = {
      source  = "registry.terraform.io/cloudflare/cloudflare"
      version = "~> 3.33.1"
    }
  }
}

locals {
  # Removing trailing dot from domain - just to be sure :)
  domain_name = trimsuffix(var.domain_name, ".")
}

module "acm" {
  source = "terraform-aws-modules/acm/aws"

  domain_name = local.domain_name
  zone_id     = data.cloudflare_zone.this.id

  create_route53_records  = false
  validation_record_fqdns = cloudflare_record.validation[*].hostname

  tags = {
    Name        = local.domain_name
    ServiceName = var.service_name
    Env         = var.env
  }
}

resource "cloudflare_record" "validation" {
  count = length(module.acm.distinct_domain_names)

  zone_id = data.cloudflare_zone.this.id
  name    = element(module.acm.validation_domains, count.index)["resource_record_name"]
  type    = element(module.acm.validation_domains, count.index)["resource_record_type"]
  value   = trimsuffix(element(module.acm.validation_domains, count.index)["resource_record_value"], ".")
  ttl     = 60
  proxied = false

  allow_overwrite = true
}

data "cloudflare_zone" "this" {
  name = var.cloudflare_zone
}