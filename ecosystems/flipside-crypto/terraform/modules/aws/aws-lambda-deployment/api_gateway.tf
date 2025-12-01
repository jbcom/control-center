# API Gateway v2 integration for Lambda functions
# This file adds API Gateway support to the aws-lambda-deployment module

locals {
  create_api_gateway = var.create_api_gateway && module.this.enabled

  # Determine the Lambda function URI based on the integration type
  lambda_function_uri = local.create_api_gateway ? (
    var.api_gateway_lambda_integration_type == "function" ? aws_lambda_function.this[0].invoke_arn : (
      var.api_gateway_lambda_integration_type == "alias" ? (
        var.create_alias && var.api_gateway_lambda_alias_name != null ?
        "${aws_lambda_function.this[0].invoke_arn}:${var.api_gateway_lambda_alias_name}" :
        aws_lambda_function.this[0].invoke_arn
        ) : (
        var.api_gateway_lambda_integration_type == "version" && var.api_gateway_lambda_version != null ?
        "${aws_lambda_function.this[0].invoke_arn}:${var.api_gateway_lambda_version}" :
        aws_lambda_function.this[0].invoke_arn
      )
    )
  ) : null

  # Determine the Lambda function qualifier based on the integration type
  lambda_function_qualifier = local.create_api_gateway ? (
    var.api_gateway_lambda_integration_type == "function" ? null : (
      var.api_gateway_lambda_integration_type == "alias" ? (
        var.create_alias && var.api_gateway_lambda_alias_name != null ?
        var.api_gateway_lambda_alias_name : null
        ) : (
        var.api_gateway_lambda_integration_type == "version" && var.api_gateway_lambda_version != null ?
        var.api_gateway_lambda_version : null
      )
    )
  ) : null

  # List of all possible Lambda function ARNs for IAM policy
  lambda_function_arns = local.create_api_gateway ? compact([
    aws_lambda_function.this[0].arn,
    var.create_alias && var.api_gateway_lambda_alias_name != null ?
    "${aws_lambda_function.this[0].arn}:${var.api_gateway_lambda_alias_name}" : null,
    var.api_gateway_lambda_version != null ?
    "${aws_lambda_function.this[0].arn}:${var.api_gateway_lambda_version}" : null
  ]) : []

  # Enhanced API Gateway log group name generation
  api_gateway_log_group_name = var.api_gateway_access_log_settings.log_group_name != null ? var.api_gateway_access_log_settings.log_group_name : (
    var.api_gateway_create_log_group ? "/aws/apigateway/${module.this.id}-api-access-logs" : null
  )

  # Enhanced API Gateway log group ARN generation
  api_gateway_log_group_arn = var.api_gateway_access_log_settings.destination_arn != null ? var.api_gateway_access_log_settings.destination_arn : (
    var.api_gateway_create_log_group ? aws_cloudwatch_log_group.api_gateway_logs[0].arn : null
  )

  # Enhanced API Gateway stage access log settings
  api_gateway_stage_access_log_settings = var.api_gateway_access_log_settings != null ? merge(
    var.api_gateway_access_log_settings,
    {
      # Only set destination_arn if it's not already set and we're creating a log group
      destination_arn = local.api_gateway_log_group_arn
    }
  ) : null
}

# API Gateway v2 for HTTP APIs
module "api_gateway" {
  source  = "terraform-aws-modules/apigateway-v2/aws"
  version = "5.4.1"

  count = local.create_api_gateway ? 1 : 0

  name          = var.api_gateway_name != null ? var.api_gateway_name : "${module.this.id}-api"
  description   = var.api_gateway_description != null ? var.api_gateway_description : "API Gateway for ${module.this.id} Lambda function"
  protocol_type = var.api_gateway_protocol_type

  # Domain name configuration
  create_domain_name          = var.api_gateway_create_domain_name
  domain_name                 = var.api_gateway_domain_name
  domain_name_certificate_arn = local.api_gateway_effective_certificate_arn
  create_domain_records       = var.api_gateway_create_domain_records
  hosted_zone_name            = local.api_gateway_effective_hosted_zone_name

  # Stage configuration
  create_stage = var.api_gateway_create_stage
  stage_name   = var.api_gateway_stage_name

  # Access logs configuration
  stage_access_log_settings = local.api_gateway_stage_access_log_settings

  # Default stage settings
  stage_default_route_settings = var.api_gateway_default_route_settings

  # Authorizers configuration
  authorizers = var.api_gateway_authorizers

  # Routes configuration with integrations
  routes = {
    for route_key, route_config in var.api_gateway_routes : route_key => merge(
      route_config,
      {
        integration = merge(
          route_config.integration,
          var.api_gateway_auto_set_lambda_uri && try(route_config.integration.uri, null) == null ? {
            # Default to the appropriate Lambda function URI if URI is not provided and auto-set is enabled
            uri = local.lambda_function_uri
          } : {}
        )
      }
    )
  }

  # CORS configuration
  cors_configuration = var.api_gateway_cors_configuration

  # Tags
  tags = module.this.tags
}

# CloudWatch log group for API Gateway access logs
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  count = local.create_api_gateway && var.api_gateway_create_log_group ? 1 : 0

  name              = local.api_gateway_log_group_name
  retention_in_days = coalesce(var.api_gateway_access_log_settings.log_group_retention_in_days, local.effective_cloudwatch_logs_retention_in_days)
  kms_key_id        = coalesce(var.api_gateway_access_log_settings.log_group_kms_key_id, local.effective_cloudwatch_logs_kms_key_id)
  skip_destroy      = var.api_gateway_access_log_settings.log_group_skip_destroy
  tags              = merge(module.this.tags, var.api_gateway_access_log_settings.log_group_tags)
}

# IAM role for API Gateway to invoke the Lambda function
resource "aws_iam_role" "api_gateway_execution_role" {
  count = local.create_api_gateway && var.api_gateway_create_execution_role ? 1 : 0

  name = "${module.this.id}-api-execution-role"
  path = "/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
    }]
  })

  tags = module.this.tags
}

# IAM policy for API Gateway to invoke the Lambda function
resource "aws_iam_role_policy" "api_gateway_execution_policy" {
  count = local.create_api_gateway && var.api_gateway_create_execution_role ? 1 : 0

  name = "${module.this.id}-api-execution-policy"
  role = aws_iam_role.api_gateway_execution_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "lambda:InvokeFunction"
      Effect   = "Allow"
      Resource = local.lambda_function_arns
    }]
  })
}

# Lambda permission for API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "api_gateway_lambda" {
  count = local.create_api_gateway ? 1 : 0

  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this[0].function_name
  qualifier     = local.lambda_function_qualifier
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${try(module.api_gateway[0].api_execution_arn, "")}/*"
}
