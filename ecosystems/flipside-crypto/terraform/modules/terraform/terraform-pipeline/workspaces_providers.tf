# Complete provider processing moved to Python for better maintainability
module "providers_config" {
  source = "../terraform-get-terraform-pipeline-providers-config"

  workspaces_template_variables_config = local.workspaces_template_variables_config
  workspace_sops_config                = local.workspace_sops_config
}

# Use the comprehensive provider configuration from Python
locals {
  providers_tf_json = module.providers_config.providers_tf_json
}
