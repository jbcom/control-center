resource "aws_acm_certificate" "route53" {
  domain_name       = local.zone_name
  validation_method = "DNS"

  subject_alternative_names = ["*.${local.zone_name}"]

  tags = local.tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.route53.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  name    = each.value.name
  records = [each.value.record]
  ttl     = 60
  type    = each.value.type
  zone_id = local.zone_id

  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "route53" {
  certificate_arn         = aws_acm_certificate.route53.arn
  validation_record_fqdns = [for record in aws_route53_record.validation : record.fqdn]
}

module "copilot_environment_certificates" {
  for_each = local.domains_config["cloudflare"]
  source   = "../copilot_environment_certificates"

  cloudflare_domain = each.value

  tags = local.tags
}
