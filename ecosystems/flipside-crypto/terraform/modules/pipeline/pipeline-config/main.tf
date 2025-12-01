locals {
  pipeline_kms_config = merge({
    enabled               = false
    managed               = false
    generated_kms_key_arn = format("arn:%s:kms:us-east-1:%s:alias/%s", local.partition, local.account_id, var.pipeline_name)
  }, lookup(var.config, "kms", {}))

  secrets_kms_key_arn = local.pipeline_kms_config["enabled"] ? local.pipeline_kms_config["generated_kms_key_arn"] : ""

  terraform_raw_config = lookup(var.config, "terraform", {})

  configured_backend_bucket_workspaces_path = try(var.config["terraform"]["backend"]["backend_bucket_workspaces_path"], null)

  terraform_backend_config = merge(var.terraform_backend, lookup(local.terraform_raw_config, "backend", {}), {
    backend_bucket_workspaces_path = coalesce(local.configured_backend_bucket_workspaces_path, "terraform/state/${var.pipeline_name}/workspaces")
  })

  backend_bucket_workspaces_path = local.terraform_backend_config["backend_bucket_workspaces_path"]

  terraform_workspace_raw_config = lookup(local.terraform_raw_config, "workspace", {})

  terraform_workspace_base_config = merge(local.terraform_workspace_raw_config, local.terraform_backend_config, {
    secrets_kms_key_arn = local.secrets_kms_key_arn
  })

  terraform_workspace_context_binding = lookup(local.terraform_workspace_base_config, "bind_to_context", {})

  terraform_workflow_base_config = lookup(local.terraform_raw_config, "workflow", {})

  terraform_workflow_config = merge(local.terraform_workflow_base_config, {
    workflow_name = lookup(local.terraform_workflow_base_config, "workflow_name", var.pipeline_name)
  })

  terraform_generator_raw_config = merge({
    enabled = true
  }, lookup(local.terraform_raw_config, "generator", {}))

  file_base_path = lookup(var.config, "file_base_path", "repository-files/${var.pipeline_name}")

  terraform_generator_workspace_raw_config = lookup(local.terraform_generator_raw_config, "workspace", {})
}

module "terraform_generator_workspace_config" {
  source = "../../utils/deepmerge"

  source_maps = [
    {
      workspace_name = "generator"
    },
    local.terraform_backend_config,
    {
      bind_to_context = local.terraform_workspace_context_binding
    },
    local.terraform_generator_workspace_raw_config,
  ]
}

locals {
  terraform_generator_workspace_config = module.terraform_generator_workspace_config.merged_maps

  terraform_generator_config = {
    workspace = merge(local.terraform_generator_workspace_config, {
      secrets_kms_key_arn = local.secrets_kms_key_arn
    })

    workflow = lookup(local.terraform_generator_raw_config, "workflow", {
      workflow_name = "generator"
    })
  }

  terraform_workspace_config = merge(local.terraform_workspace_base_config, {
    bind_to_context = merge(local.terraform_workspace_context_binding, {
      state_path = lookup(local.terraform_workspace_context_binding, "state_path", format("%s/%s/terraform.tfstate", local.backend_bucket_workspaces_path, lookup(local.terraform_generator_workspace_config, "backend_workspace_name", local.terraform_generator_workspace_config["workspace_name"])))
    })
  })

  terraform_base_config = {
    enabled = merge(local.terraform_raw_config, {
      enabled   = true
      backend   = local.terraform_backend_config
      workspace = local.terraform_workspace_config
      workflow  = local.terraform_workflow_config
      generator = local.terraform_generator_config
    })

    disabled = {}
  }

  terraform_config_key = lookup(local.terraform_raw_config, "enabled", false) ? "enabled" : "disabled"

  terraform_config = local.terraform_base_config[local.terraform_config_key]

  use_sync                   = lookup(var.config, "use_sync", false)
  existing_repository_name   = try(coalesce(var.config.existing_repository_name, var.pipeline_name), var.pipeline_name)
  existing_repository_branch = try(coalesce(var.config.existing_repository_branch), "main")

  gitops_config = merge(var.config, {
    use_sync = local.use_sync

    pipeline_name = var.pipeline_name

    file_base_path = local.file_base_path

    kms = local.pipeline_kms_config

    terraform = local.terraform_config

    repository = {
      name           = local.existing_repository_name
      default_branch = local.existing_repository_branch
    }
  })
}
