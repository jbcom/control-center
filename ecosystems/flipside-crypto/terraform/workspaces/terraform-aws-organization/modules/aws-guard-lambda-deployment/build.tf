# Guard lambda function
module "guard_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.0.1"

  # Conditional creation using module's built-in parameters
  create          = local.enabled_from_cloudposse_context
  create_package  = local.enabled_from_cloudposse_context
  create_function = local.enabled_from_cloudposse_context
  create_role     = local.enabled_from_cloudposse_context

  function_name = local.function_name
  description   = local.lambda_config_from_repo_context.description
  handler       = local.lambda_config_from_repo_context.handler
  runtime       = local.lambda_config_from_repo_context.runtime
  architectures = local.lambda_config_from_repo_context.architectures

  # Performance and reliability settings
  timeout                        = local.lambda_config_from_repo_context.timeout
  memory_size                    = local.lambda_config_from_repo_context.memory_size
  reserved_concurrent_executions = local.reserved_concurrency_from_repo_context
  publish                        = true

  # Enhanced logging configuration
  cloudwatch_logs_retention_in_days  = local.logs_retention_days_from_repo_context
  cloudwatch_logs_log_group_class    = local.logs_log_group_class_from_repo_context
  attach_cloudwatch_logs_policy      = local.enabled_from_cloudposse_context
  attach_create_log_group_permission = local.enabled_from_cloudposse_context

  # Optimized source path configuration following module best practices
  source_path = local.source_path_from_repo_context

  # Build configuration for CI/CD environments
  artifacts_dir = local.artifacts_dir_from_repo_context

  # CI/CD optimizations
  recreate_missing_package     = false
  trigger_on_package_timestamp = false

  # Environment variables
  environment_variables = local.environment_variables_from_repo_context

  # Enhanced IAM permissions with least privilege
  attach_policy_statements = local.enabled_from_cloudposse_context && length(local.policy_statements_from_repo_context) > 0
  policy_statements        = local.policy_statements_from_repo_context

  # Dead letter queue for failed executions
  attach_dead_letter_policy = local.enabled_from_cloudposse_context
  dead_letter_target_arn    = local.enabled_from_cloudposse_context ? aws_sqs_queue.guard_dlq[0].arn : null

  # Async event configuration for better error handling
  create_async_event_config    = local.enabled_from_cloudposse_context
  maximum_retry_attempts       = local.max_retry_attempts_from_repo_context
  maximum_event_age_in_seconds = local.max_event_age_seconds_from_repo_context
  destination_on_failure       = local.enabled_from_cloudposse_context ? aws_sqs_queue.guard_dlq[0].arn : null

  # Enhanced security and performance
  kms_key_arn = local.kms_key_arn_from_repo_context

  # Tracing configuration for debugging
  attach_tracing_policy = local.attach_tracing_policy_from_repo_context
  tracing_mode          = local.tracing_mode_from_repo_context

  # Comprehensive tagging
  tags = merge(local.tags_from_cloudposse_context, local.guard_config_from_repo_context.tags)
}

# EventBridge rule to trigger the lambda
resource "aws_cloudwatch_event_rule" "guard_schedule" {
  count = local.enabled_from_cloudposse_context ? 1 : 0

  name                = "${local.function_name}-schedule"
  description         = local.schedule_config_from_repo_context.description
  schedule_expression = local.schedule_config_from_repo_context.expression

  tags = local.tags_from_cloudposse_context
}

# EventBridge target to invoke the lambda alias
resource "aws_cloudwatch_event_target" "guard_target" {
  count = local.enabled_from_cloudposse_context ? 1 : 0

  rule      = aws_cloudwatch_event_rule.guard_schedule[0].name
  target_id = "${local.function_name}-target"
  arn       = module.guard_alias.lambda_alias_arn
}
