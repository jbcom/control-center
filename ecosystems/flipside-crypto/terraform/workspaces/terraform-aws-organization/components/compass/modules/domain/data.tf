data "aws_route53_zone" "selected" {
  name = var.context["domains"]["route53"]
}

locals {
  cloudflare_domain = var.context["domains"]["cloudflare"][var.environment_name]
}

data "cloudflare_zone" "selected" {
  name = "${local.cloudflare_domain}."
}

locals {
  copilot_zone_id = data.cloudflare_zone.selected.zone_id
}

data "aws_lb" "copilot_managed" {
  tags = {
    copilot-application = "compass"
    copilot-environment = var.environment_name
  }
}

locals {
  copilot_lb_dns_name = lower(data.aws_lb.copilot_managed.dns_name)
}
