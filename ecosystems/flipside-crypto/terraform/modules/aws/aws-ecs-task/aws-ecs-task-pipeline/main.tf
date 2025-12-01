locals {
  pipeline_name = coalesce(var.config.name, var.name)

  files_data = [
    {
      ".github/workflows" = {
        "${local.pipeline_name}.yml" = templatefile("${path.module}/templates/workflow.yml", merge(var.config, {
          pipeline_name = local.pipeline_name
        }))
      }
    }
  ]
}