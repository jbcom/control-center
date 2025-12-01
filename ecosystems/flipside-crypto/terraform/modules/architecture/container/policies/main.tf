locals {
  environment_name = var.context["environment"]
}

module "default" {
  for_each = var.context["task_deployments"]

  source = "./policies-task"

  task_name         = each.key
  deployment_config = each.value

  context = var.context
}