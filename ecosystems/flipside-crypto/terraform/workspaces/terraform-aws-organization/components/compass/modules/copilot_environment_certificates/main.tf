resource "aws_acm_certificate" "cloudflare" {
  domain_name       = "*.${var.cloudflare_domain}"
  validation_method = "DNS"

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "cloudflare_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.cloudflare.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }


  zone_id = local.cloudflare_zone_id
  name    = each.value["name"]
  value   = each.value["record"]
  type    = each.value["type"]
  proxied = false
  ttl     = 60
}

resource "aws_acm_certificate_validation" "default" {
  certificate_arn         = aws_acm_certificate.cloudflare.arn
  validation_record_fqdns = [for record in cloudflare_record.validation : record.hostname]
}
