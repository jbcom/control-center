locals {
  tags = merge(var.context["tags"], {
    Mame = var.zone_name
  })
}

resource "aws_acm_certificate" "default" {
  domain_name = var.zone_name

  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.zone_name}",
  ]

  tags = local.tags

  lifecycle {
    create_before_destroy = true
  }
}

locals {
  acm_certificate_arn = aws_acm_certificate.default.arn
}

resource "cloudflare_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.default.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    } if dvo.domain_name == var.zone_name
  }

  zone_id = var.zone_id
  name    = each.value["name"]
  value   = each.value["record"]
  type    = each.value["type"]
  ttl     = 60

  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "default" {
  certificate_arn         = local.acm_certificate_arn
  validation_record_fqdns = [for record in cloudflare_record.validation : record["hostname"]]
}

locals {
  redirects_config = try(var.context["redirects"][var.zone_name], {})
}

module "cloudfront_redirect" {
  providers = {
    aws            = aws
    aws.cloudfront = aws.cloudfront
  }

  for_each = local.redirects_config

  source = "../../cloudfront/cloudfront-redirect"

  name                = "${each.key}.${var.zone_name}"
  redirect_target     = each.value
  acm_certificate_arn = local.acm_certificate_arn

  context = var.context
}

resource "cloudflare_record" "redirect" {
  for_each = module.cloudfront_redirect

  zone_id = var.zone_id
  name    = "${each.key}.${var.zone_name}"
  value   = each.value.domain_name
  type    = "CNAME"
  ttl     = 600

  allow_overwrite = true
}