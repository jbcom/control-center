locals {
  workflow_file = templatefile("${path.module}/templates/sync.yml", merge(var.config, {
    workflow_name = trimsuffix(var.config.workflow_file_name, ".yml")
  }))

  sync_config = {
    for repository_name, repository_targets in var.config.repositories : (var.config.repository_owner != "" ? "${var.config.repository_owner}/${repository_name}" : repository_name) => concat(repository_targets, var.config.sync_to_all)
  }

  files = [
    {
      ".github/workflows" = {
        (var.config.workflow_file_name) = local.workflow_file
      }

      (dirname(var.config.config_path)) = {
        (basename(var.config.config_path)) = replace(yamlencode(local.sync_config), "/((?:^|\n)[\\s-]*)\"([\\w-]+)\":/", "$1$2:")
      }
    }
  ]
}

module "files" {
  count = var.save_files ? 1 : 0

  source = "../../files"

  files = local.files

  rel_to_root = var.rel_to_root
}