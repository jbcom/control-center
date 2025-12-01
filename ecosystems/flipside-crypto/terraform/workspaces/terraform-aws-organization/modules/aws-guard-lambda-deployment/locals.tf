locals {
  # CloudPosse context outputs (naming, tagging, enablement)
  enabled_from_cloudposse_context = module.this.enabled
  id_from_cloudposse_context      = module.this.id
  tags_from_cloudposse_context    = module.this.tags

  # Repository context configurations (our blackbox)
  root_config_from_repo_context     = var.context
  guard_config_from_repo_context    = var.context.guards[var.name]
  admin_bot_users_from_repo_context = var.context.admin_bot_users
  kms_config_from_repo_context      = var.context.kms

  # Derived values
  function_name = "${local.id_from_cloudposse_context}-guard"

  # Build configuration with defaults
  build_config_from_repo_context = {
    artifacts_dir         = try(local.guard_config_from_repo_context.build.artifacts_dir, "builds/guards")
    attach_tracing_policy = try(local.guard_config_from_repo_context.build.attach_tracing_policy, false)
    kms_key_arn           = try(local.guard_config_from_repo_context.build.kms_key_arn, null)
    tracing_mode          = try(local.guard_config_from_repo_context.build.tracing_mode, null)
  }

  # Deploy configuration with defaults
  deploy_config_from_repo_context = {
    config_name                = try(local.guard_config_from_repo_context.deploy.config_name, "CodeDeployDefault.Lambda10PercentEvery5Minutes")
    force_deploy               = try(local.guard_config_from_repo_context.deploy.force_deploy, false)
    save_deploy_script         = try(local.guard_config_from_repo_context.deploy.save_deploy_script, true)
    wait_deployment_completion = try(local.guard_config_from_repo_context.deploy.wait_deployment_completion, true)
    auto_rollback_enabled      = try(local.guard_config_from_repo_context.deploy.auto_rollback_enabled, true)
    auto_rollback_events       = try(local.guard_config_from_repo_context.deploy.auto_rollback_events, ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"])
    alarm_enabled              = try(local.guard_config_from_repo_context.deploy.alarm_enabled, false)
    alarms                     = try(local.guard_config_from_repo_context.deploy.alarms, [])
  }

  # Monitoring configuration with defaults
  monitoring_config_from_repo_context = {
    cloudwatch_logs_retention_days  = try(local.guard_config_from_repo_context.monitoring.cloudwatch_logs_retention_days, 30)
    cloudwatch_logs_log_group_class = try(local.guard_config_from_repo_context.monitoring.cloudwatch_logs_log_group_class, "STANDARD")
    maximum_retry_attempts          = try(local.guard_config_from_repo_context.monitoring.maximum_retry_attempts, 2)
    maximum_event_age_in_seconds    = try(local.guard_config_from_repo_context.monitoring.maximum_event_age_in_seconds, 3600)
    dlq_message_retention_seconds   = try(local.guard_config_from_repo_context.monitoring.dlq_message_retention_seconds, 1209600) # 14 days
  }

  # Performance configuration with defaults
  performance_config_from_repo_context = {
    reserved_concurrent_executions = try(local.guard_config_from_repo_context.performance.reserved_concurrent_executions, 1)
  }

  # Lambda configuration with defaults
  lambda_config_from_repo_context = {
    description   = try(local.guard_config_from_repo_context.lambda.description, "Guard lambda function")
    handler       = try(local.guard_config_from_repo_context.lambda.handler, "bootstrap")
    runtime       = try(local.guard_config_from_repo_context.lambda.runtime, "provided.al2023")
    architectures = try(local.guard_config_from_repo_context.lambda.architectures, ["arm64"])
    timeout       = try(local.guard_config_from_repo_context.lambda.timeout, 300)
    memory_size   = try(local.guard_config_from_repo_context.lambda.memory_size, 512)
  }

  # Schedule configuration with defaults
  schedule_config_from_repo_context = {
    expression  = try(local.guard_config_from_repo_context.schedule.expression, "rate(1 day)")
    description = try(local.guard_config_from_repo_context.schedule.description, "Trigger guard lambda daily")
  }

  # Environment variables with admin bot users injected
  environment_variables_from_repo_context = merge(
    local.guard_config_from_repo_context.environment,
    {
      ADMIN_BOT_USERS = jsonencode(local.admin_bot_users_from_repo_context)
    }
  )

  # Source path configuration
  source_path_from_repo_context = [
    {
      path = "${var.rel_to_root}/${var.base_src_dir}/${var.name}"
      commands = [
        "GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o bootstrap main.go",
        ":zip",
      ]
      patterns = [
        "!.*",
        "bootstrap",
      ]
    }
  ]

  # Policy statements with admin bot users condition
  policy_statements_from_repo_context = {
    for key, policy in local.guard_config_from_repo_context.policy_statements : key => merge(
      policy,
      key == "iam_write" && can(policy.condition) ? {
        condition = {
          for condition_key, condition_value in policy.condition : condition_key => merge(
            condition_value,
            {
              values = local.admin_bot_users_from_repo_context
            }
          )
        }
      } : {}
    )
  }

  # Security configuration locals
  kms_key_arn_from_repo_context           = coalesce(local.build_config_from_repo_context.kms_key_arn, local.kms_config_from_repo_context.arn)
  attach_tracing_policy_from_repo_context = local.build_config_from_repo_context.attach_tracing_policy
  tracing_mode_from_repo_context          = local.build_config_from_repo_context.tracing_mode

  # Frequently accessed nested configurations for main.tf
  artifacts_dir_from_repo_context = local.build_config_from_repo_context.artifacts_dir

  # Deploy configuration locals
  deployment_config_name_from_repo_context = local.deploy_config_from_repo_context.config_name
  force_deploy_from_repo_context           = local.deploy_config_from_repo_context.force_deploy
  save_deploy_script_from_repo_context     = local.deploy_config_from_repo_context.save_deploy_script
  wait_completion_from_repo_context        = local.deploy_config_from_repo_context.wait_deployment_completion

  # Monitoring configuration locals
  logs_retention_days_from_repo_context   = local.monitoring_config_from_repo_context.cloudwatch_logs_retention_days
  logs_log_group_class_from_repo_context  = local.monitoring_config_from_repo_context.cloudwatch_logs_log_group_class
  max_retry_attempts_from_repo_context    = local.monitoring_config_from_repo_context.maximum_retry_attempts
  max_event_age_seconds_from_repo_context = local.monitoring_config_from_repo_context.maximum_event_age_in_seconds
  dlq_retention_seconds_from_repo_context = local.monitoring_config_from_repo_context.dlq_message_retention_seconds

  # Performance configuration locals
  reserved_concurrency_from_repo_context = local.performance_config_from_repo_context.reserved_concurrent_executions
}
