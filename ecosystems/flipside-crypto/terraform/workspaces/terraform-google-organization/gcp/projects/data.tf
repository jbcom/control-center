data "google_client_config" "default" {}

locals {
  google_region = data.google_client_config.default.region
}

data "google_organization" "org" {
  organization = "organizations/${local.org_id}"
}
