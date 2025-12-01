module "task_secrets_config" {
  source = "../../../../../utils/deepmerge"

  source_maps = [
    var.task_config["secrets"],
    {
      vendors = local.datadog_vendor_secret_names_map
    }
  ]
}

module "task_secrets" {
  source = "../../../secrets"

  config = module.task_secrets_config.merged_maps

  secret_manager_name_prefix = "tasks/${var.task_name}"

  context = var.context

  rel_to_root = var.rel_to_root
}

module "task_environment_variables" {
  source = "../../../environment-variables"

  config = var.task_config["environment_variables"]

  context = var.context

  rel_to_root = var.rel_to_root
}

locals {
  task_environment_variables = module.task_environment_variables.environment_variables
}
