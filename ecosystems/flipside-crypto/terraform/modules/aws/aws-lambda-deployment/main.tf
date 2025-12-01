locals {
  function_name = coalesce(var.function_name, module.this.id)
  ecr_repo_name = coalesce(var.ecr_repository_name, local.function_name)

  # Determine if we're using a container image
  is_container = var.package_type == "Image"

  # Determine if we need to create a package
  create_package = !local.is_container && var.local_existing_package == null && var.s3_existing_package == null

  # Determine if we need to create a deployment
  create_deployment = var.create_deploy && var.create_alias

  # Determine if we need to create a deployment group
  deployment_group_name = coalesce(var.deployment_group_name, "${local.function_name}-deploy-group")

  # Determine if we need to create an app
  app_name = "${local.function_name}-app"

  # Determine if we need to create an ECR repository
  create_ecr_repo = module.this.enabled && local.is_container && var.create_ecr_repository

  # Determine if we need to build a Docker image
  create_docker_build = module.this.enabled && local.is_container && var.create_docker_build

  # Default ECR lifecycle policy
  default_ecr_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "Keep last 30 images",
        selection = {
          tagStatus   = "any",
          countType   = "imageCountMoreThan",
          countNumber = 30
        },
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# ECR Repository for container images
resource "aws_ecr_repository" "this" {
  count = local.create_ecr_repo ? 1 : 0

  name                 = local.ecr_repo_name
  image_tag_mutability = var.ecr_image_tag_mutability
  force_delete         = var.ecr_force_delete

  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }

  tags = merge(module.this.tags, var.ecr_repository_tags)
}

resource "aws_ecr_lifecycle_policy" "this" {
  count = local.create_ecr_repo ? 1 : 0

  repository = aws_ecr_repository.this[0].name
  policy     = coalesce(var.ecr_repository_lifecycle_policy, local.default_ecr_lifecycle_policy)
}

# Docker image build
module "docker_image" {
  source  = "terraform-aws-modules/lambda/aws//modules/docker-build"
  version = "8.1.2"

  count = local.create_docker_build ? 1 : 0

  create_ecr_repo = false
  ecr_repo        = local.create_ecr_repo ? aws_ecr_repository.this[0].name : local.ecr_repo_name

  use_image_tag = var.use_image_tag
  image_tag     = var.image_tag

  source_path      = var.source_path
  docker_file_path = var.docker_file_path
  build_args       = var.build_args
}

# Lambda Function
module "lambda_function" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.2"

  create = module.this.enabled

  function_name = local.function_name
  description   = var.description
  handler       = var.handler
  runtime       = var.runtime
  architectures = var.architectures
  memory_size   = var.memory_size
  timeout       = var.timeout
  publish       = var.publish

  # Package configuration
  package_type = var.package_type

  # Container image configuration
  image_uri                      = local.create_docker_build ? module.docker_image[0].image_uri : var.image_uri
  image_config_entry_point       = var.image_config_entry_point
  image_config_command           = var.image_config_command
  image_config_working_directory = var.image_config_working_directory

  # Source code configuration
  create_package         = local.create_package
  source_path            = var.source_path
  local_existing_package = var.local_existing_package
  s3_existing_package    = var.s3_existing_package

  # Environment variables
  environment_variables = var.environment_variables

  # Lambda@Edge configuration
  lambda_at_edge                  = var.lambda_at_edge
  lambda_at_edge_logs_all_regions = var.lambda_at_edge_logs_all_regions

  # VPC configuration
  vpc_subnet_ids         = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids
  attach_network_policy  = var.attach_network_policy

  # IAM role configuration
  create_role               = var.create_role
  lambda_role               = var.lambda_role
  role_name                 = var.role_name
  role_description          = var.role_description
  role_path                 = var.role_path
  role_permissions_boundary = var.role_permissions_boundary
  role_tags                 = var.role_tags

  # IAM policy configuration
  policy_statements             = var.policy_statements
  attach_policy_statements      = var.attach_policy_statements
  attach_cloudwatch_logs_policy = var.attach_cloudwatch_logs_policy
  attach_dead_letter_policy     = var.attach_dead_letter_policy
  attach_tracing_policy         = var.attach_tracing_policy
  dead_letter_target_arn        = var.dead_letter_target_arn
  trusted_entities              = var.trusted_entities

  # CloudWatch logs configuration
  cloudwatch_logs_retention_in_days = local.effective_cloudwatch_logs_retention_in_days
  cloudwatch_logs_kms_key_id        = local.effective_cloudwatch_logs_kms_key_id
  use_existing_cloudwatch_log_group = var.use_existing_cloudwatch_log_group

  # Function URL configuration
  create_lambda_function_url = var.create_lambda_function_url
  authorization_type         = var.authorization_type
  cors                       = var.cors
  invoke_mode                = var.invoke_mode

  # Async event configuration
  create_async_event_config    = var.create_async_event_config
  maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
  maximum_retry_attempts       = var.maximum_retry_attempts
  destination_on_failure       = var.destination_on_failure
  destination_on_success       = var.destination_on_success

  # Event source mapping
  event_source_mapping = var.event_source_mapping

  # Allowed triggers
  allowed_triggers                          = var.allowed_triggers
  create_current_version_allowed_triggers   = var.create_current_version_allowed_triggers
  create_unqualified_alias_allowed_triggers = var.create_unqualified_alias_allowed_triggers

  # Provisioned concurrency
  provisioned_concurrent_executions = var.provisioned_concurrent_executions

  # Logging configuration
  logging_log_format            = var.logging_log_format
  logging_application_log_level = var.logging_application_log_level
  logging_system_log_level      = var.logging_system_log_level

  # File system configuration
  file_system_arn              = var.file_system_arn
  file_system_local_mount_path = var.file_system_local_mount_path

  # Timeouts
  timeouts = var.timeouts

  # Skip destroy
  skip_destroy = var.skip_destroy

  # Tags
  tags          = module.this.tags
  function_tags = var.function_tags
}

# Lambda Alias
module "lambda_alias" {
  source  = "terraform-aws-modules/lambda/aws//modules/alias"
  version = "8.1.2"

  create = module.this.enabled && var.create_alias

  name          = var.alias_name
  function_name = module.lambda_function.lambda_function_name

  # Set function_version when creating alias to be able to deploy using it
  function_version = var.create_version_alias ? module.lambda_function.lambda_function_version : null

  # Allowed triggers for this alias
  allowed_triggers = var.allowed_triggers

  # Async event configuration
  create_async_event_config    = var.create_async_event_config
  maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
  maximum_retry_attempts       = var.maximum_retry_attempts
  destination_on_failure       = var.destination_on_failure
  destination_on_success       = var.destination_on_success
}

# Lambda Deployment via AWS CodeDeploy
module "lambda_deploy" {
  source  = "terraform-aws-modules/lambda/aws//modules/deploy"
  version = "8.1.2"

  create = module.this.enabled && local.create_deployment

  alias_name    = module.lambda_alias.lambda_alias_name
  function_name = module.lambda_function.lambda_function_name

  target_version = module.lambda_function.lambda_function_version

  create_app = true
  app_name   = local.app_name

  create_deployment_group = true
  deployment_group_name   = local.deployment_group_name

  deployment_config_name = var.deployment_config_name

  auto_rollback_enabled = var.auto_rollback_enabled
  auto_rollback_events  = var.auto_rollback_events

  # Don't automatically run deployment as part of this module
  create_deployment          = false
  run_deployment             = false
  wait_deployment_completion = false
}

# CloudWatch Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = module.this.enabled && var.create_cloudwatch_alarm ? 1 : 0

  alarm_name          = coalesce(var.cloudwatch_alarm_name, "${module.lambda_function.lambda_function_name}-errors")
  comparison_operator = var.cloudwatch_alarm_comparison_operator
  evaluation_periods  = var.cloudwatch_alarm_evaluation_periods
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.cloudwatch_alarm_period
  statistic           = var.cloudwatch_alarm_statistic
  threshold           = var.cloudwatch_alarm_threshold
  alarm_description   = coalesce(var.cloudwatch_alarm_description, "This alarm monitors for errors in the ${module.lambda_function.lambda_function_name} Lambda function")

  dimensions = {
    FunctionName = module.lambda_function.lambda_function_name
    Resource     = "${module.lambda_function.lambda_function_name}:${module.lambda_alias.lambda_alias_name}"
  }

  tags = merge(module.this.tags, var.cloudwatch_alarm_tags)
}

# SSM Parameters
locals {
  ssm_parameter_prefix = var.use_ssm_parameter_prefix ? coalesce(var.ssm_parameter_prefix, "/${local.function_name}/") : ""

  # Process SSM parameter names
  ssm_parameter_names = {
    for k, v in var.ssm_parameters : k => {
      # Use provided name if available, otherwise use the map key
      name = coalesce(v.name, var.use_ssm_parameter_prefix ? "${local.ssm_parameter_prefix}${k}" : k)
      # Pass through all other values
      value       = v.value
      type        = v.type
      description = v.description
      overwrite   = v.overwrite
      key_id      = v.key_id
    }
  }
}

resource "aws_ssm_parameter" "this" {
  for_each = module.this.enabled && var.create_ssm_parameters ? toset(keys(var.ssm_parameters)) : []

  name        = local.ssm_parameter_names[each.key].name
  description = local.ssm_parameter_names[each.key].description
  type        = local.ssm_parameter_names[each.key].type
  value       = local.ssm_parameter_names[each.key].value
  overwrite   = local.ssm_parameter_names[each.key].overwrite
  key_id      = coalesce(local.ssm_parameter_names[each.key].key_id, local.effective_kms_key_arn)

  tags = module.this.tags
}

# Additional IAM Role Policy Attachments
resource "aws_iam_role_policy_attachment" "additional" {
  count = module.this.enabled && var.create_role ? length(var.additional_iam_role_policy_arns) : 0

  role       = module.lambda_function.lambda_role_name
  policy_arn = var.additional_iam_role_policy_arns[count.index]
}

# Additional Lambda Permissions
resource "aws_lambda_permission" "additional" {
  count = module.this.enabled ? length(var.additional_lambda_permissions) : 0

  function_name = module.lambda_function.lambda_function_name

  statement_id       = var.additional_lambda_permissions[count.index].statement_id
  action             = var.additional_lambda_permissions[count.index].action
  principal          = var.additional_lambda_permissions[count.index].principal
  source_arn         = var.additional_lambda_permissions[count.index].source_arn
  source_account     = var.additional_lambda_permissions[count.index].source_account
  event_source_token = var.additional_lambda_permissions[count.index].event_source_token
  qualifier          = var.additional_lambda_permissions[count.index].qualifier != null ? var.additional_lambda_permissions[count.index].qualifier : module.lambda_alias.lambda_alias_name
}
