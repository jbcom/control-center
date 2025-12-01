resource "aws_route53_record" "route53_rpc_environment_alias" {
  zone_id         = data.aws_route53_zone.selected.zone_id
  name            = "rpc-${var.environment_name}"
  type            = "A"
  allow_overwrite = true

  alias {
    name                   = local.copilot_lb_dns_name
    zone_id                = data.aws_lb.copilot_managed.zone_id
    evaluate_target_health = true
  }
}

resource "cloudflare_record" "cloudflare_rpc_alias" {
  zone_id         = local.copilot_zone_id
  name            = "rpc"
  value           = local.copilot_lb_dns_name
  type            = "CNAME"
  proxied         = false
  allow_overwrite = true
}

resource "cloudflare_record" "cloudflare_rpc_environment_alias" {
  zone_id         = local.copilot_zone_id
  name            = "rpc-${var.environment_name}"
  value           = local.copilot_lb_dns_name
  type            = "CNAME"
  proxied         = false
  allow_overwrite = true
}
