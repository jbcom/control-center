locals {
  help_target = file("${path.module}/files/help.mk")
}

resource "local_sensitive_file" "copilot_makefile" {
  filename = "${var.rel_to_root}/copilot/copilot.mk"

  content = templatefile("${path.module}/templates/makefiles/copilot.mk", {
    zone_name               = local.zone_name
    compass_assume_role_arn = local.compass_assume_role_arn
    copilot_assume_role_arn = module.copilot_execution_role.arn
    region                  = local.region
    help_target             = local.help_target
  })
}

resource "local_sensitive_file" "services_makefile" {
  filename = "${var.rel_to_root}/copilot/Makefile"

  content = templatefile("${path.module}/templates/makefiles/services.mk", {
    environments = local.compass_environments
    services     = keys(local.service_manifests_config)
    help_target  = local.help_target
  })
}

locals {
  env_to_branch_map = {
    stg  = "staging"
    prod = "main"
  }
}
resource "local_sensitive_file" "pipelines_makefile" {
  filename = "${var.rel_to_root}/copilot/pipelines/Makefile"

  content = templatefile("${path.module}/templates/makefiles/pipelines.mk", {
    environments      = local.compass_environments
    env_to_branch_map = local.env_to_branch_map
    services          = keys(local.service_manifests_config)
    help_target       = local.help_target
  })
}
