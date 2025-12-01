locals {
  environment_name = var.context["environment"]
  tags             = var.context["tags"]

  account_data = var.context["cluster_accounts_by_environment"][local.environment_name]
  json_key     = local.account_data["json_key"]

  networking_data    = var.context["cluster_networks"][local.json_key]
  vpc_id             = local.networking_data["vpc_id"]
  private_subnet_ids = local.networking_data["private_subnet_ids"]
  public_subnet_ids  = local.networking_data["public_subnet_ids"]

  allowed_cidr_blocks = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
  ]

  system_environment_data = var.context["system_environment"]

  task_environment_data = local.system_environment_data["tasks"][var.task_name]
  task_context          = local.task_environment_data["context"]
  task_tags = {
    for k, v in local.system_environment_data["task_tags"][var.task_name] : title(k) => v if lower(k) != "name" && !startswith(lower(k), "aws:")
  }

  containers_config = {
    for _, container_config in var.task_config["containers"] : container_config["name"] => merge(container_config, {
      tag = lookup(container_config, "tag", "latest")
    })
  }

  task_containers_config = var.task_config["containers"]

  task_permissions_config = var.task_config["permissions"]

  task_launch_environments = lookup(var.task_config, "launch_environments", [
    local.environment_name,
  ])

  task_enabled  = var.task_config["enabled"]
  task_exposed  = var.task_config["exposed"]
  task_launched = local.task_enabled && var.task_config["launched"] && contains(local.task_launch_environments, local.environment_name)
}

locals {
  ecs_task_policy_arns = compact(concat(local.task_permissions_config["policy_attachments"], [
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
  ]))

  cluster_config = var.context["clusters"][local.environment_name]
  cluster_name   = local.cluster_config["cluster_name"]
  cluster_arn    = local.cluster_config["cluster_arn"]

  default_capacity_provider_strategy = local.cluster_config["default_capacity_provider_strategy"]
  default_capacity_provider_weight   = local.default_capacity_provider_strategy["weight"]

  spot_capacity_provider_config  = lookup(var.task_config, "spot", {})
  spot_capacity_provider_enabled = lookup(local.spot_capacity_provider_config, "enabled", false)
  spot_capacity_provider_weight  = lookup(local.spot_capacity_provider_config, "weight", 0)

  mixed_capacity_provider_weight_difference = local.default_capacity_provider_weight - local.spot_capacity_provider_weight

  capacity_provider_base_strategies = {
    all_spot = [
      {
        base              = 1
        weight            = 100
        capacity_provider = "FARGATE_SPOT"
      },
    ]

    mixed_spot = [
      merge(local.default_capacity_provider_strategy, {
        weight = local.mixed_capacity_provider_weight_difference
        }), {
        base              = null
        weight            = local.spot_capacity_provider_weight
        capacity_provider = "FARGATE_SPOT"
      },
    ]

    no_spot = [
      local.default_capacity_provider_strategy,
    ]
  }

  capacity_provider_key = local.spot_capacity_provider_enabled ? (local.spot_capacity_provider_weight == 100 ? "all_spot" : "mixed_spot") : "no_spot"

  capacity_provider_strategies = local.capacity_provider_base_strategies[local.capacity_provider_key]

  deployment_config = var.task_config["deployment"]

  task_circuit_breaker_config = var.task_config["circuit_breaker"]

  service_name = module.ecs_service_task.service_name

  autoscaling_config    = var.task_config["autoscaling"]
  autoscaling_enabled   = local.task_launched && local.autoscaling_config["enabled"]
  autoscaling_dimension = local.autoscaling_config["dimension"]
}

module "ecs_service_task" {
  source  = "cloudposse/ecs-alb-service-task/aws"
  version = "0.78.0"

  enabled = local.task_launched

  ecs_service_enabled = lookup(var.task_config, "service_enabled", true)

  container_definition_json = jsonencode(local.container_definitions)

  ecs_cluster_arn = local.cluster_arn

  ecs_load_balancers = local.container_load_balancer_targets

  launch_type = "FARGATE"

  capacity_provider_strategies = local.capacity_provider_strategies

  circuit_breaker_deployment_enabled = local.task_circuit_breaker_config["enabled"]
  circuit_breaker_rollback_enabled   = local.task_circuit_breaker_config["rollback"]

  vpc_id       = local.vpc_id
  subnet_ids   = local.private_subnet_ids
  network_mode = "awsvpc"

  alb_security_group     = var.task_config["exposed"] ? local.alb_security_group_id : null
  use_alb_security_group = false

  desired_count                      = local.deployment_config["desired_count"]
  deployment_maximum_percent         = local.deployment_config["maximum_percent"]
  deployment_minimum_healthy_percent = local.deployment_config["minimum_healthy_percent"]

  task_memory = var.task_config.memory
  task_cpu    = var.task_config.cpu

  ephemeral_storage_size = var.task_config["ephemeral_storage_size"]

  efs_volumes = local.efs_filesystem_data

  task_policy_arns      = local.ecs_task_policy_arns
  task_exec_policy_arns = local.ecs_task_policy_arns

  ignore_changes_task_definition = false
  ignore_changes_desired_count   = local.autoscaling_enabled

  enable_ecs_managed_tags = true

  wait_for_steady_state = var.task_config["wait_for_steady_state"]

  force_new_deployment = false

  context = local.task_context
}

locals {
  secrets_kms_key_arn = "arn:aws:kms:us-east-1:862006574860:key/ec033500-c790-4c62-9a2e-c1daf091041d"
}

resource "aws_kms_grant" "task_role" {
  count = local.task_launched ? 1 : 0

  grantee_principal = module.ecs_service_task.task_role_arn

  key_id = local.secrets_kms_key_arn

  operations = [
    "Decrypt",
    "Encrypt",
  ]
}

resource "aws_kms_grant" "task_exec_role" {
  count = local.task_launched ? 1 : 0

  grantee_principal = module.ecs_service_task.task_exec_role_arn

  key_id = local.secrets_kms_key_arn

  operations = [
    "Decrypt",
    "Encrypt",
  ]
}

locals {
  task_definition_arn = module.ecs_service_task.task_definition_arn

  unique_container_ports = distinct(flatten([
    for container_definition in local.container_definitions : [
      for port_mapping_config in try(container_definition["portMappings"], []) : join("/", [port_mapping_config["protocol"], port_mapping_config["containerPort"]]) if local.task_exposed
    ]
  ]))
}

locals {
  task_identifiers = compact([
    module.ecs_service_task.task_role_arn,
    module.ecs_service_task.task_exec_role_arn,
  ])
}


module "ecs_cloudwatch_autoscaling" {
  source  = "cloudposse/ecs-cloudwatch-autoscaling/aws"
  version = "1.0.0"

  enabled = local.task_launched && local.autoscaling_enabled

  service_name          = local.service_name
  cluster_name          = local.cluster_name
  min_capacity          = local.autoscaling_config["min_capacity"]
  max_capacity          = local.autoscaling_config["max_capacity"]
  scale_up_adjustment   = local.autoscaling_config["scale_up_adjustment"]
  scale_up_cooldown     = local.autoscaling_config["scale_up_cooldown"]
  scale_down_adjustment = local.autoscaling_config["scale_down_adjustment"]
  scale_down_cooldown   = local.autoscaling_config["scale_down_cooldown"]

  context = local.task_context
}

locals {
  alarms_config  = var.task_config["alarms"]
  alarms_enabled = local.task_launched && local.alarms_config["enabled"]

  cpu_utilization_high_alarm_actions    = local.autoscaling_enabled && local.autoscaling_dimension == "cpu" ? module.ecs_cloudwatch_autoscaling.scale_up_policy_arn : ""
  cpu_utilization_low_alarm_actions     = local.autoscaling_enabled && local.autoscaling_dimension == "cpu" ? module.ecs_cloudwatch_autoscaling.scale_down_policy_arn : ""
  memory_utilization_high_alarm_actions = local.autoscaling_enabled && local.autoscaling_dimension == "memory" ? module.ecs_cloudwatch_autoscaling.scale_up_policy_arn : ""
  memory_utilization_low_alarm_actions  = local.autoscaling_enabled && local.autoscaling_dimension == "memory" ? module.ecs_cloudwatch_autoscaling.scale_down_policy_arn : ""
}

module "ecs_cloudwatch_sns_alarms" {
  source  = "cloudposse/ecs-cloudwatch-sns-alarms/aws"
  version = "0.13.2"

  enabled = local.alarms_enabled

  attributes = ["ecs"]

  cluster_name = local.cluster_name
  service_name = local.service_name

  cpu_utilization_high_threshold          = local.alarms_config["ecs_cpu_utilization_high_threshold"]
  cpu_utilization_high_evaluation_periods = local.alarms_config["ecs_cpu_utilization_high_evaluation_periods"]
  cpu_utilization_high_period             = local.alarms_config["ecs_cpu_utilization_high_period"]

  cpu_utilization_high_alarm_actions = compact(
    concat(
      local.alarms_config["ecs_cpu_utilization_high_alarm_actions"],
      [local.cpu_utilization_high_alarm_actions],
    )
  )

  cpu_utilization_high_ok_actions = local.alarms_config["ecs_cpu_utilization_high_ok_actions"]

  cpu_utilization_low_threshold          = local.alarms_config["ecs_cpu_utilization_low_threshold"]
  cpu_utilization_low_evaluation_periods = local.alarms_config["ecs_cpu_utilization_low_evaluation_periods"]
  cpu_utilization_low_period             = local.alarms_config["ecs_cpu_utilization_low_period"]

  cpu_utilization_low_alarm_actions = compact(
    concat(
      local.alarms_config["ecs_cpu_utilization_low_alarm_actions"],
      [local.cpu_utilization_low_alarm_actions],
    )
  )

  cpu_utilization_low_ok_actions = local.alarms_config["ecs_cpu_utilization_low_ok_actions"]

  memory_utilization_high_threshold          = local.alarms_config["ecs_memory_utilization_high_threshold"]
  memory_utilization_high_evaluation_periods = local.alarms_config["ecs_memory_utilization_high_evaluation_periods"]
  memory_utilization_high_period             = local.alarms_config["ecs_memory_utilization_high_period"]

  memory_utilization_high_alarm_actions = compact(
    concat(
      local.alarms_config["ecs_memory_utilization_high_alarm_actions"],
      [local.memory_utilization_high_alarm_actions],
    )
  )

  memory_utilization_high_ok_actions = local.alarms_config["ecs_memory_utilization_high_ok_actions"]

  memory_utilization_low_threshold          = local.alarms_config["ecs_memory_utilization_low_threshold"]
  memory_utilization_low_evaluation_periods = local.alarms_config["ecs_memory_utilization_low_evaluation_periods"]
  memory_utilization_low_period             = local.alarms_config["ecs_memory_utilization_low_period"]

  memory_utilization_low_alarm_actions = compact(
    concat(
      local.alarms_config["ecs_memory_utilization_low_alarm_actions"],
      [local.memory_utilization_low_alarm_actions],
    )
  )

  memory_utilization_low_ok_actions = local.alarms_config["ecs_memory_utilization_low_ok_actions"]

  context = local.task_context
}
