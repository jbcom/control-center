# Lambda alias for controlled deployments
module "guard_alias" {
  source  = "terraform-aws-modules/lambda/aws//modules/alias"
  version = "8.0.1"

  # Conditional creation using module's built-in parameters
  create                                    = local.enabled_from_cloudposse_context
  create_qualified_alias_allowed_triggers   = local.enabled_from_cloudposse_context
  create_qualified_alias_async_event_config = local.enabled_from_cloudposse_context

  refresh_alias = true
  name          = "current"
  description   = "Current version alias for ${local.function_name}"

  function_name    = module.guard_lambda.lambda_function_name
  function_version = module.guard_lambda.lambda_function_version

  # Use alias for EventBridge triggers
  allowed_triggers = local.enabled_from_cloudposse_context ? {
    EventBridge = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.guard_schedule[0].arn
    }
  } : {}

  # Async event configuration for the alias
  maximum_retry_attempts       = local.max_retry_attempts_from_repo_context
  maximum_event_age_in_seconds = local.max_event_age_seconds_from_repo_context
  destination_on_failure       = local.enabled_from_cloudposse_context ? aws_sqs_queue.guard_dlq[0].arn : null
}

# CodeDeploy for controlled lambda deployments
module "guard_deploy" {
  source  = "terraform-aws-modules/lambda/aws//modules/deploy"
  version = "8.0.1"

  # Conditional creation using module's built-in parameters
  create                  = local.enabled_from_cloudposse_context
  create_app              = local.enabled_from_cloudposse_context
  create_deployment_group = local.enabled_from_cloudposse_context

  alias_name     = module.guard_alias.lambda_alias_name
  function_name  = module.guard_lambda.lambda_function_name
  target_version = module.guard_lambda.lambda_function_version

  description = "Controlled deployment of ${local.function_name} guard lambda"

  # CodeDeploy application and deployment group
  app_name              = "${local.function_name}-app"
  deployment_group_name = "${local.function_name}-dg"

  # Deployment configuration
  create_deployment          = local.enabled_from_cloudposse_context
  run_deployment             = local.enabled_from_cloudposse_context
  save_deploy_script         = local.save_deploy_script_from_repo_context
  wait_deployment_completion = local.wait_completion_from_repo_context
  force_deploy               = local.force_deploy_from_repo_context

  # Use gradual deployment for safety
  deployment_config_name = local.deployment_config_name_from_repo_context

  # Auto-rollback configuration for enhanced safety
  auto_rollback_enabled = local.deploy_config_from_repo_context.auto_rollback_enabled
  auto_rollback_events  = local.deploy_config_from_repo_context.auto_rollback_events

  # CloudWatch alarm integration for deployment monitoring
  alarm_enabled = local.deploy_config_from_repo_context.alarm_enabled
  alarms        = local.deploy_config_from_repo_context.alarms

  # Deployment notifications
  attach_triggers_policy = local.enabled_from_cloudposse_context
  triggers = local.enabled_from_cloudposse_context ? {
    deployment_start = {
      events     = ["DeploymentStart"]
      name       = "DeploymentStart"
      target_arn = aws_sns_topic.deployment_notifications[0].arn
    }
    deployment_success = {
      events     = ["DeploymentSuccess"]
      name       = "DeploymentSuccess"
      target_arn = aws_sns_topic.deployment_notifications[0].arn
    }
    deployment_failure = {
      events     = ["DeploymentFailure", "DeploymentStop", "DeploymentRollback"]
      name       = "DeploymentFailure"
      target_arn = aws_sns_topic.deployment_failures[0].arn
    }
    deployment_ready = {
      events     = ["DeploymentReady"]
      name       = "DeploymentReady"
      target_arn = aws_sns_topic.deployment_notifications[0].arn
    }
  } : {}

  tags = local.tags_from_cloudposse_context
}

# SNS topics for deployment notifications
resource "aws_sns_topic" "deployment_notifications" {
  count = local.enabled_from_cloudposse_context ? 1 : 0
  name  = "${local.function_name}-deployment-notifications"

  tags = local.tags_from_cloudposse_context
}

resource "aws_sns_topic" "deployment_failures" {
  count = local.enabled_from_cloudposse_context ? 1 : 0
  name  = "${local.function_name}-deployment-failures"

  tags = local.tags_from_cloudposse_context
}
