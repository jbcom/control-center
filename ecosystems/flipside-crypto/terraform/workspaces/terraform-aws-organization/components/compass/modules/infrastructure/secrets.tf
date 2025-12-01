resource "doppler_project" "default" {
  name        = "compass"
  description = "The Compass project"
}

module "environment_secrets" {
  for_each = toset(local.compass_environments)

  source = "./infrastructure-secrets"

  environment_name = each.key

  doppler_project = doppler_project.default.name

  tags = local.copilot_environment_tags[each.key]

  context = var.context
}

resource "aws_ssm_parameter" "dockerhub" {
  for_each = toset(["username", "password"])

  name        = "/thorchain/midgard/${local.environment_name}/secrets/dockerhub_${each.key}"
  type        = "SecureString"
  value       = var.vendors["dockerhub_${each.key}"]
  description = format("Docker Hub ${each.key} for Midgard")
  tags        = var.context["tags"]
}
