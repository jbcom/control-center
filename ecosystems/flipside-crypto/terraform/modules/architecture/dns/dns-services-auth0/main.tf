resource "auth0_custom_domain" "cloudflare" {
  for_each = toset(var.config.cloudflare_domains)

  domain = "login.${each.key}"
  type   = "auth0_managed_certs"
}

data "cloudflare_zone" "selected" {
  for_each = auth0_custom_domain.cloudflare

  name = each.key
}

resource "cloudflare_record" "auth0" {
  for_each = auth0_custom_domain.cloudflare

  zone_id         = data.cloudflare_zone.selected[each.key].zone_id
  name            = "${each.value.domain}."
  value           = "${each.value.verification[0].methods[0].record}."
  type            = upper(each.value.verification[0].methods[0].name)
  allow_overwrite = true
  ttl             = 300
}

resource "auth0_custom_domain_verification" "cloudflare" {
  for_each = auth0_custom_domain.cloudflare

  custom_domain_id = each.value.id

  timeouts { create = "15m" }

  depends_on = [cloudflare_record.auth0]
}

resource "auth0_custom_domain" "route53" {
  for_each = toset(var.config.route53_domains)

  domain = "login.${each.key}"
  type   = "auth0_managed_certs"
}

data "aws_route53_zone" "selected" {
  for_each = auth0_custom_domain.route53

  name = each.key
}

resource "aws_route53_record" "auth0" {
  for_each = auth0_custom_domain.route53

  zone_id = data.aws_route53_zone.selected[each.key].zone_id
  name    = "${each.value.domain}."
  records = ["${each.value.verification[0].methods[0].record}."]
  type    = upper(each.value.verification[0].methods[0].name)
  ttl     = 300
}

resource "auth0_custom_domain_verification" "route53" {
  for_each = auth0_custom_domain.route53

  custom_domain_id = each.value.id

  timeouts { create = "15m" }

  depends_on = [aws_route53_record.auth0]
}