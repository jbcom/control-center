output "workflow" {
  value = var.workflow

  description = "Workflow configuration"
}

output "workspace_dirs" {
  value = local.workspaces_workspace_dir

  description = "Workspace directories"
}

output "workspace_dirs_by_job_name" {
  value = local.workspaces_workspace_dir_by_job_name

  description = "Workspace directories by job name"
}

output "workspaces" {
  value = local.pipeline_workspaces

  description = "Workspaces configuration"
}

output "files" {
  value = local.pipeline_files

  description = "Pipeline files data"
}

output "preserve_names_as_is" {
  value = local.preserve_names_as_is

  description = "Preserve names as is"
}