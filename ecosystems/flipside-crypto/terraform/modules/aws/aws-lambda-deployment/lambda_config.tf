# Lambda Configuration Defaults
# This file defines the default configuration for Lambda functions

locals {
  # Lambda configuration defaults
  lambda_defaults = {
    enabled               = true
    function_name         = null
    description           = null
    handler               = null
    runtime               = "nodejs18.x"
    memory_size           = 128
    timeout               = 3
    publish               = true
    package_type          = "Zip"
    architectures         = ["x86_64"]
    environment_variables = {}
    tags                  = {}

    # Lambda@Edge specific settings
    lambda_at_edge                  = false
    lambda_at_edge_logs_all_regions = false

    # Deployment configuration
    create_package         = true
    local_existing_package = null
    source_path            = null

    # Container image configuration
    create_ecr_repository    = false
    ecr_repository_name      = null
    ecr_image_tag_mutability = "MUTABLE"
    ecr_scan_on_push         = true
    ecr_force_delete         = false

    # Docker build configuration
    create_docker_build = false
    docker_file_path    = "Dockerfile"
    image_tag           = null
    build_args          = {}

    # IAM role configuration
    create_role              = true
    role_name                = null
    role_description         = null
    role_path                = "/service-role/"
    role_tags                = {}
    trusted_entities         = []
    attach_policy_statements = false
    policy_statements        = {}

    # CloudWatch logs configuration
    attach_cloudwatch_logs_policy     = true
    cloudwatch_logs_retention_in_days = 14
    cloudwatch_logs_kms_key_id        = null

    # CloudWatch Alarm Configuration
    create_cloudwatch_alarm              = false
    cloudwatch_alarm_name                = null
    cloudwatch_alarm_description         = null
    cloudwatch_alarm_threshold           = 0
    cloudwatch_alarm_evaluation_periods  = 1
    cloudwatch_alarm_period              = 60
    cloudwatch_alarm_statistic           = "Sum"
    cloudwatch_alarm_comparison_operator = "GreaterThanThreshold"
    cloudwatch_alarm_tags                = {}

    # Tracing and monitoring
    tracing_mode          = null
    attach_tracing_policy = false

    # Deployment configuration
    create_alias           = false
    alias_name             = null
    create_deploy          = false
    deployment_config_name = "CodeDeployDefault.LambdaAllAtOnce"
    auto_rollback_enabled  = true
    auto_rollback_events   = ["DEPLOYMENT_FAILURE"]

    # Logging configuration
    logging_log_format            = "JSON"
    logging_application_log_level = "INFO"
    logging_system_log_level      = "INFO"

    # Timeouts for resource operations
    timeouts = {
      create = "10m"
      update = "10m"
      delete = "10m"
    }
  }

  # Final lambda configuration with individual variable overrides
  lambda = merge(
    local.config.lambda,
    {
      function_name                     = var.function_name != null ? var.function_name : local.config.lambda.function_name
      description                       = var.description != null ? var.description : local.config.lambda.description
      handler                           = var.handler != null ? var.handler : local.config.lambda.handler
      runtime                           = var.runtime != null ? var.runtime : local.config.lambda.runtime
      memory_size                       = var.memory_size != null ? var.memory_size : local.config.lambda.memory_size
      timeout                           = var.timeout != null ? var.timeout : local.config.lambda.timeout
      publish                           = var.publish != null ? var.publish : local.config.lambda.publish
      package_type                      = var.package_type != null ? var.package_type : local.config.lambda.package_type
      architectures                     = var.architectures != null ? var.architectures : local.config.lambda.architectures
      environment_variables             = var.environment_variables != null ? var.environment_variables : local.config.lambda.environment_variables
      lambda_at_edge                    = var.lambda_at_edge != null ? var.lambda_at_edge : local.config.lambda.lambda_at_edge
      lambda_at_edge_logs_all_regions   = var.lambda_at_edge_logs_all_regions != null ? var.lambda_at_edge_logs_all_regions : local.config.lambda.lambda_at_edge_logs_all_regions
      create_package                    = var.create_package != null ? var.create_package : local.config.lambda.create_package
      local_existing_package            = var.local_existing_package != null ? var.local_existing_package : local.config.lambda.local_existing_package
      source_path                       = var.source_path != null ? var.source_path : local.config.lambda.source_path
      create_role                       = var.create_role != null ? var.create_role : local.config.lambda.create_role
      role_name                         = var.role_name != null ? var.role_name : local.config.lambda.role_name
      role_description                  = var.role_description != null ? var.role_description : local.config.lambda.role_description
      role_path                         = var.role_path != null ? var.role_path : local.config.lambda.role_path
      trusted_entities                  = var.trusted_entities != null ? var.trusted_entities : local.config.lambda.trusted_entities
      attach_policy_statements          = var.attach_policy_statements != null ? var.attach_policy_statements : local.config.lambda.attach_policy_statements
      policy_statements                 = var.policy_statements != null ? var.policy_statements : local.config.lambda.policy_statements
      cloudwatch_logs_retention_in_days = var.cloudwatch_logs_retention_in_days != null ? var.cloudwatch_logs_retention_in_days : local.effective_cloudwatch_logs_retention_in_days
      cloudwatch_logs_kms_key_id        = var.cloudwatch_logs_kms_key_id != null ? var.cloudwatch_logs_kms_key_id : local.effective_cloudwatch_logs_kms_key_id
      create_cloudwatch_alarm           = var.create_cloudwatch_alarm != null ? var.create_cloudwatch_alarm : local.config.lambda.create_cloudwatch_alarm
      cloudwatch_alarm_name             = var.cloudwatch_alarm_name != null ? var.cloudwatch_alarm_name : local.config.lambda.cloudwatch_alarm_name
      cloudwatch_alarm_description      = var.cloudwatch_alarm_description != null ? var.cloudwatch_alarm_description : local.config.lambda.cloudwatch_alarm_description
      tracing_mode                      = var.tracing_mode != null ? var.tracing_mode : local.config.lambda.tracing_mode
      attach_tracing_policy             = var.attach_tracing_policy != null ? var.attach_tracing_policy : local.config.lambda.attach_tracing_policy
      create_alias                      = var.create_alias != null ? var.create_alias : local.config.lambda.create_alias
      alias_name                        = var.alias_name != null ? var.alias_name : local.config.lambda.alias_name
      create_deploy                     = var.create_deploy != null ? var.create_deploy : local.config.lambda.create_deploy
      deployment_config_name            = var.deployment_config_name != null ? var.deployment_config_name : local.config.lambda.deployment_config_name
    }
  )
}
