module "ecr_repository" {
  source  = "cloudposse/ecr/aws"
  version = "1.0.0"

  image_names = toset(var.repository_names)

  enabled = length(var.repository_names) > 0

  use_fullname = false

  scan_images_on_push  = true
  image_tag_mutability = "MUTABLE"

  principals_full_access = var.context["admin_principals"]

  context = var.context
}

module "repository_build_config" {
  for_each = {
    for repository_name, repository_url in module.ecr_repository.repository_url_map : repository_name => [
      for task_name, task_config in var.tasks : merge(try(coalesce(task_config["pipeline"]["build"]), {}), {
        tasks = [task_name]
        }) if anytrue([
        for _, container_config in task_config["containers"] : (container_config["repository_name"] == repository_name)
      ])
    ]
  }

  source = "../../../../utils/deepmerge"

  source_maps = each.value
}

locals {
  repository_build_config = {
    for repository_name, merge_results in module.repository_build_config : repository_name => merge_results.merged_maps
  }
}
