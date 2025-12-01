data "cloudflare_zone" "selected" {
  name = "${var.cloudflare_domain}."
}

locals {
  cloudflare_zone_id = data.cloudflare_zone.selected.zone_id
}
