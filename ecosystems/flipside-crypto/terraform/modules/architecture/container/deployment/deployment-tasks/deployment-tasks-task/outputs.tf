output "task" {
  value = merge(module.ecs_service_task, {
    task_security_group_id = local.alb_security_group_id
    task_launched          = local.task_launched
    unique_container_ports = local.unique_container_ports
    task_policy_arn        = module.task_policy.policy_arn
    task_tags              = local.task_tags
    dd_tags                = local.dd_tags
  })

  description = "Task data"
}

output "load_balancer" {
  value = local.load_balancer_data

  description = "Load balancer data"
}

output "filesystems" {
  value = {
    for filesystem_id, filesystem_data in local.task_filesystems : filesystem_id =>
    merge(filesystem_data, {
      policy_arns = distinct(compact(concat(filesystem_data["external_policy_identifier_arns"], local.task_identifiers)))
    })
  }


  description = "Filesystems data"
}

output "identifiers" {
  value = local.task_identifiers

  description = "ECS task identifiers"
}

output "secrets" {
  value = {
    for _, secret_arn in module.task_secrets.map_secrets : secret_arn => local.task_identifiers
    if local.task_launched && length(local.task_identifiers) > 0
  }

  description = "Secrets to bind to task identifiers"
}