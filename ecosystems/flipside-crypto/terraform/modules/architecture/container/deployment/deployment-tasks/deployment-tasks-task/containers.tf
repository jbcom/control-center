locals {
  container_repository_tags = {
    for container_name, container_definition in local.task_containers_config :
    container_name => try(coalesce(container_definition["tag"]), "latest")
  }

  container_repository_names = {
    for container_name, container_definition in local.task_containers_config :
    container_name => container_definition["repository_name"]
  }

  container_repository_urls = {
    for container_name, container_definition in local.task_containers_config :
    container_name =>
    try(coalesce(container_definition["image"]), null) != null ? container_definition["image"] : var.repository_images[container_definition["repository_name"]]["name"]
  }

  container_repository_images = {
    for container_name, repository_url in local.container_repository_urls :
    container_name =>
    strcontains(repository_url, ":") ? repository_url : format("%s:%s", repository_url, local.container_repository_tags[container_name])
  }

  task_log_configuration = {
    logDriver = "awsfirelens"
    options = {
      Name           = "datadog"
      Host           = "http-intake.logs.datadoghq.com"
      TLS            = "on"
      dd_service     = var.task_name
      dd_source      = "ecs-fargate"
      dd_message_key = "log"
      dd_tags        = local.dd_tags
      provider       = "ecs"
    }

    secretOptions = [
      {
        name      = "apikey"
        valueFrom = local.datadog_container_secrets["DD_API_KEY"]
      }
    ]
  }
}

module "container_definition" {
  for_each = {
    for container_name, container_definition in local.task_containers_config :
    container_name => container_definition
    if try(container_definition["launched"], local.task_launched)
  }

  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.61.2"

  container_name               = each.key
  container_image              = local.container_repository_images[each.key]
  container_cpu                = each.value["cpu"]
  container_memory             = each.value["memory"]
  container_memory_reservation = lookup(each.value, "memory_reservation", null)

  command    = each.value["command"]
  entrypoint = each.value["entrypoint"]

  container_depends_on = each.value["container_depends_on"]

  disable_networking = each.value["disable_networking"]

  dns_search_domains = each.value["dns_search_domains"]
  dns_servers        = each.value["dns_servers"]

  essential = each.value["essential"]

  extra_hosts = each.value["extra_hosts"]

  links = each.value["links"]

  linux_parameters = each.value["linux_parameters"]

  readonly_root_filesystem = each.value["readonly_root_filesystem"]

  start_timeout = each.value["start_timeout"]
  stop_timeout  = each.value["stop_timeout"]

  system_controls = each.value["system_controls"]

  ulimits = each.value["ulimits"]

  user = each.value["user"]

  volumes_from = each.value["volumes_from"]

  working_directory = each.value["working_directory"]

  port_mappings = each.value["port_mappings"]

  secrets = module.task_secrets.secrets

  environment = local.task_environment_variables

  log_configuration = local.task_log_configuration

  mount_points = local.mount_point_data
}

locals {
  container_definitions = concat([
    for _, container_data in module.container_definition : container_data["json_map_object"]
    ], [
    module.container_definition_datadog_agent.json_map_object,
    module.container_definition_fluentbit.json_map_object,
  ])
}