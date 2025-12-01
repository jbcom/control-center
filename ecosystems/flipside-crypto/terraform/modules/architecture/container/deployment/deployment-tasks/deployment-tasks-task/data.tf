data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

data "aws_region" "current" {}

locals {
  region = data.aws_region.current.name

  cloudflare_domain = lookup(var.task_config, "cloudflare_domain", "")
}

data "cloudflare_zone" "selected" {
  count = local.cloudflare_domain != "" ? 1 : 0

  name = "${var.task_config.cloudflare_domain}."
}

locals {
  cloudflare_zone = join("", data.cloudflare_zone.selected.*.zone_id)
}
