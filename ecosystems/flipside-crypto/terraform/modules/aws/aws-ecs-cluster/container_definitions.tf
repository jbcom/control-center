locals {
  container_log_configuration = {
    logDriver = "awsfirelens"

    secretOptions = [
      {
        name      = "apikey"
        valueFrom = local.datadog_data["map_secrets"]["DD_API_KEY"]
      }
    ]
  }

  container_log_options = {
    Name        = "datadog"
    Host        = "http-intake.logs.datadoghq.com"
    dd_source   = var.cluster_name
    dd_tags     = "ecs-cluster:${var.cluster_name}"
    TLS         = "on"
    provider    = "ecs"
    retry_limit = 2
  }
}

module "container_definition_datadog_agent" {
  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.61.2"

  container_name   = "datadog-agent"
  container_image  = "public.ecr.aws/datadog/agent:latest"
  container_cpu    = 256
  container_memory = 512

  environment = var.cluster_config.launch_type == "FARGATE" ? [
    {
      name  = "ECS_FARGATE"
      value = true
    }
  ] : []

  secrets = local.datadog_data["secrets"]

  log_configuration = merge(local.container_log_configuration, {
    options = merge(local.container_log_options, {
      dd_source = "datadog-agent"
    })
  })
}

module "container_definition_log_router" {
  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.61.2"

  container_name  = "log_router"
  container_image = "amazon/aws-for-fluent-bit:stable"
  essential       = true

  firelens_configuration = {
    type = "fluentbit"

    options = {
      enable-ecs-log-metadata = true
    }
  }

  container_memory_reservation = 100

  log_configuration = merge(local.container_log_configuration, {
    options = merge(local.container_log_options, {
      dd_source = "log_router"
    })
  })
}

module "container_definition" {
  for_each = var.cluster_config.containers

  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.61.2"

  container_name               = each.value["name"]
  container_image              = each.value["image"]
  container_cpu                = lookup(each.value, "cpu", null)
  container_memory             = lookup(each.value, "memory", null)
  container_memory_reservation = lookup(each.value, "memory_reservation", null)
  start_timeout                = lookup(each.value, "start_timeout", null)

  port_mappings = lookup(each.value, "port_mappings", [])

  log_configuration = merge(local.container_log_configuration, {
    options = merge(local.container_log_options, {
      dd_source = each.value["name"]
    })
  })

  mount_points = [
    for container_path, volume_data in module.efs : {
      containerPath = container_path
      sourceVolume  = replace(container_path, "/", "-")
      readOnly      = false
    }
  ]

  container_depends_on = [
    {
      containerName = "datadog-agent"
      condition     = "HEALTHY"
    },
    {
      containerName = "log_router"
      condition     = "HEALTHY"
    }
  ]
}