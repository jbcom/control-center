output "files" {
  value = local.files_data

  description = "Pipeline files"
}

output "group_name" {
  value = coalesce(var.config.stage, var.config.environment)

  description = "Group name for the shared calling workflow"
}

output "workflow_file_path" {
  value = ".github/workflows/${local.pipeline_name}.yml"
}