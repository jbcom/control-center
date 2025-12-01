locals {
  environment_name     = var.pipeline_config["environment"]
  shared_pipeline_name = var.pipeline_config["shared_pipeline_name"]
  tasks                = var.pipeline_config["tasks"]

  cluster_accounts_by_environment_data = var.context["cluster_accounts_by_environment"]
  cluster_account                      = local.cluster_accounts_by_environment_data[local.environment_name]
  json_key                             = local.cluster_account["json_key"]
  cluster_network_local                = format("$${local.context.networks.cluster_%s}", local.json_key)

  container_config_context_prefix   = try(format("$${local.context.%s}", coalesce(trimprefix(var.context_container_config_jmes_path, "."))), "local.context")
  container_config_context_template = format("$${%s.%%s}", local.container_config_context_prefix)
}

module "terraform_workspace_config" {
  source = "../../../../utils/deepmerge"

  source_maps = [
    var.base_terraform_workspace_config,
    {
      root_dir      = format(var.base_nested_root_dir_template, "containers")
      workspace_dir = local.environment_name

      bind_to_account = local.cluster_accounts_by_environment_data[local.environment_name]["execution_role_arn"]

      bind_to_context = merge(var.base_default_context_binding, {
        environment = local.environment_name
      })

      backend_bucket_workspaces_path = format(var.base_nested_backend_path_prefix_template, "containers/${local.environment_name}")
    },
    try(var.pipeline_config["workspace"], {}),
    {

    }
  ]

  denylist = ["job_name", "workspace_name"]

  log_file_name = "${var.pipeline_name}-terraform-workspace-config.log"
}

locals {
  terraform_workspace_config = module.terraform_workspace_config.merged_maps
}

module "default_context_binding" {
  source = "../../../../utils/deepmerge"

  source_maps = [
    var.base_default_context_binding,
    try(coalesce(local.terraform_workspace_config["bind_to_context"]), {}),
    {
      environment = local.environment_name
    }
  ]

  log_file_name = "${var.pipeline_name}-terraform-workspace-config.log"
}

locals {
  default_context_binding = module.default_context_binding.merged_maps

  terraform_workspaces = {
    system-resources = merge(local.terraform_workspace_config, {
      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              source = "${var.container_modules_root}/${var.container_modules_path}/architecture/architecture-system"

              repository_names = format(local.container_config_context_template, "pipelines.${var.pipeline_name}.repository_names")

              tasks = format(local.container_config_context_template, "pipelines.${var.pipeline_name}.tasks")

              context = "$${local.context}"

              records_dir = "records/$${local.workspaces_dir}"

              rel_to_root = "$${local.rel_to_root}"
            }
          }
        })
      }
    })

    tasks = merge(local.terraform_workspace_config, {
      runner_label = "ubuntu-22-04-4-16"

      providers = [
        "cloudflare",
        "github",
      ]

      docker_images = var.pipeline_config["repositories"]

      extra_files = {
        "variables.tf.json" = jsonencode({
          variable = {
            "image_tag" = {
              description = "Docker image tag that was built prior"
              type : "string"
            }
          }
        })

        "main.tf.json" = jsonencode({
          module = {
            base = {
              source = "${var.container_modules_root}/${var.container_modules_path}/deployment/deployment-tasks"

              tasks = format(local.container_config_context_template, "pipelines.${var.pipeline_name}.tasks")

              ecr_repository_urls = format(local.container_config_context_template, "system_environment.ecr_repository_urls")

              image_tag = "$${var.image_tag}"

              context = "$${local.context}"

              records_dir = "records/$${local.workspaces_dir}"

              rel_to_root = "$${local.rel_to_root}"
            }
          }
        })
      }
    })

    policies = merge(local.terraform_workspace_config, {
      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              source = "${var.container_modules_root}/${var.container_modules_path}/policies"

              context = "$${local.context}"
            }
          }
        })
      }
    })
  }

  dependency_ordering = {
    system-resources = []

    tasks = [
      "system-resources",
    ]

    policies = [
      "tasks",
    ]
  }

  ordered_terraform_workspaces = {
    for workspace_name, workspace_config in local.terraform_workspaces : workspace_name => merge(workspace_config, {
      job_name               = workspace_name
      workspace_name         = workspace_name
      backend_workspace_name = local.shared_pipeline_name
      workspace_dir_name     = local.shared_pipeline_name

      root_dir      = "${local.terraform_workspace_config["root_dir"]}/${local.terraform_workspace_config["workspace_dir"]}"
      workspace_dir = workspace_name

      dependencies = local.dependency_ordering[workspace_name]

      bind_to_context = merge(local.default_context_binding, {
        merge_records = [
          for dep in local.dependency_ordering[workspace_name] : format("records/%s/%s/%s/%s.json", local.terraform_workspace_config["root_dir"], local.terraform_workspace_config["workspace_dir"], dep, local.shared_pipeline_name)
        ]
      })

      backend_bucket_workspaces_path = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/${workspace_name}"
    })
  }
}


module "terraform_workflow_config" {
  source = "../../../../utils/deepmerge"

  source_maps = [
    var.base_terraform_workflow_config,
    {
      workflow_name = var.pipeline_name

      events = {
        push         = true
        pull_request = false
        release      = false
      }

      autopopulate = {
        paths    = false
        branches = false
      }
    },
    try(var.pipeline_config["workflow"], {}),
  ]

  log_file_name = "${var.pipeline_name}-terraform-workflow-config.log"
}

module "pipeline" {
  source = "../../../../terraform/terraform-pipeline"

  workspaces = local.ordered_terraform_workspaces

  workflow = module.terraform_workflow_config.merged_maps

  save_files = true

  rel_to_root = var.rel_to_root
}
