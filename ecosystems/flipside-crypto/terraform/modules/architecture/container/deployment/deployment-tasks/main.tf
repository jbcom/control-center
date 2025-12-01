locals {
  environment_name = var.context["environment"]
}

module "default" {
  for_each = var.tasks

  source = "./deployment-tasks-task"

  task_name   = each.key
  task_config = each.value

  repository_images = local.repository_images

  rel_to_root = var.rel_to_root

  context = var.context
}

locals {
  task_identifiers = distinct(compact(flatten([
    for task_name, task_data in module.default : task_data["identifiers"]
    ]
  )))
}

locals {
  records_config = {
    task_deployments = module.default
  }
}

module "permanent_record" {
  source = "../../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}
