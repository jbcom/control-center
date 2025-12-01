locals {
  ecs_task_schedules = lookup(var.task_config, "schedules", [])

  task_scheduled = length(local.ecs_task_schedules) > 0
}

data "aws_iam_policy_document" "scheduled_task_exec" {
  count = local.task_scheduled ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["ecs:RunTask"]
    resources = [
      local.task_definition_arn,
    ]
  }

  statement {
    effect  = "Allow"
    actions = ["iam:PassRole"]

    resources = local.task_identifiers
  }
}

module "scheduled_task_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  attributes = concat(var.context["attributes"], ["scheduled"])

  enabled = local.task_scheduled

  policy_description = "Allow Cloudwatch to run an ECS scheduled task"
  role_description   = "Allow Cloudwatch to run an ECS scheduled task"

  principals = {
    Service = [
      "events.amazonaws.com",
      "ecs-tasks.amazonaws.com",
    ]
  }

  policy_documents = [
    join("", data.aws_iam_policy_document.scheduled_task_exec[*].json),
  ]

  context = var.context
}

resource "aws_cloudwatch_event_rule" "scheduled_task" {
  for_each = local.task_scheduled ? toset(local.ecs_task_schedules) : []

  name_prefix = "ecs-scheduled-task-"

  schedule_expression = each.key

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "scheduled_task" {
  for_each = aws_cloudwatch_event_rule.scheduled_task

  rule = each.value.name

  target_id = var.task_name
  arn       = local.cluster_arn
  role_arn  = module.scheduled_task_role.arn

  ecs_target {
    launch_type      = "FARGATE"
    platform_version = "LATEST"

    task_count          = 1
    task_definition_arn = local.task_definition_arn

    group = module.ecs_service_task.task_definition_family

    tags = local.tags

    network_configuration {
      subnets = local.private_subnet_ids

      security_groups = compact([
        local.alb_security_group_id,
      ])
    }
  }
}
