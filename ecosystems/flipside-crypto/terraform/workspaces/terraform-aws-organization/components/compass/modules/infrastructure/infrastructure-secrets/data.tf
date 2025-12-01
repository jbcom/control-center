data "doppler_secrets" "default" {
  project = var.doppler_project
  config  = doppler_config.default.name
}
