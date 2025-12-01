locals {
  pipeline_files = flatten(concat(local.workspaces_files_data, var.workflow.enable ? local.workflow_files_data : []))

  pipeline_workspaces = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => merge(workspace_config, {
      workspace_path = local.workspaces_workspace_dir[workspace_name]
    })
  }

  preserve_names_as_is = [".terragrunt.tf"]
}

module "files" {
  count = var.save_files ? 1 : 0

  source = "../../files"

  files = local.pipeline_files

  save_gitkeep_record = var.save_gitkeep_record

  preserve_names_as_is = local.preserve_names_as_is

  rel_to_root = var.rel_to_root
}

module "workflow_debug" {
  count = var.debug_dir != null ? 1 : 0

  source = "../../utils/permanent-record"

  records = var.workflow

  records_dir = pathexpand("${var.debug_dir}/${local.workflow_name}/workflow")

  records_file_name = "workflow.json"
}

module "workspaces_debug" {
  count = var.debug_dir != null ? 1 : 0

  source = "../../utils/permanent-record"

  records = local.pipeline_workspaces

  records_dir = pathexpand("${var.debug_dir}/${local.workflow_name}/workspaces")

  records_file_name = "workspaces.json"
}