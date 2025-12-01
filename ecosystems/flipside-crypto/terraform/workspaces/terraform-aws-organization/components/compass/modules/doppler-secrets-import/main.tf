locals {
  slug_to_name_map = {
    stg  = "Staging"
    prod = "Production"
  }
}

resource "doppler_environment" "default" {
  project = var.doppler_project
  slug    = var.environment_name
  name    = local.slug_to_name_map[var.environment_name]
}

resource "doppler_config" "default" {
  project     = var.doppler_project
  environment = doppler_environment.default.slug
  name        = "${var.environment_name}_copilot"
}

resource "doppler_secret" "default" {
  for_each = local.compass_environment_secrets

  project = var.doppler_project
  config  = doppler_config.default.name
  name    = each.key
  value   = each.value
}
