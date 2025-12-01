locals {
  dd_tags = join(",", compact([
    for k, v in local.task_tags : try((lower(k) == lower(v) || v == "" ? lower(k) : "${lower(k)}:${v}"), "")
  ]))

  datadog_vendor_secret_names_map = {
    DD_API_KEY = "datadog_api_key"
    DD_APP_KEY = "datadog_app_key"
  }

  datadog_container_secrets = {
    for key_name, _ in local.datadog_vendor_secret_names_map : key_name => module.task_secrets.map_secrets[key_name]
  }
}

module "container_definition_datadog_agent" {
  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.61.2"

  container_name  = "datadog-agent"
  container_image = "public.ecr.aws/datadog/agent:latest"

  container_memory_reservation = 64

  essential = true

  port_mappings = [
    {
      containerPort = 8125
      hostPort      = 8125
      protocol      = "udp"
    }
  ]

  environment = [
    {
      name  = "ECS_FARGATE"
      value = true
      }, {
      name  = "DD_ENV"
      value = local.environment_name
      }, {
      name  = "DD_TAGS"
      value = local.dd_tags
      }, {
      name  = "DD_PROCESS_AGENT_ENABLED"
      value = true
      }, {
      name  = "DD_DOGSTATSD_NON_LOCAL_TRAFFIC"
      value = true
    }
  ]

  secrets = [
    for key, arn in local.datadog_container_secrets : {
      name      = key
      valueFrom = arn
    }
  ]
}