# API Gateway Configuration Defaults
# This file defines the default configuration for API Gateway

locals {
  # API Gateway configuration defaults
  api_gateway_defaults = {
    enabled = false

    # API Gateway KMS Policy Configuration
    include_kms_policy = true

    # API Gateway Lambda Integration
    lambda_integration_type = "function"
    lambda_alias_name       = null
    lambda_version          = null
    auto_set_lambda_uri     = true

    # API Gateway Configuration
    name          = null
    description   = null
    protocol_type = "HTTP"

    # Domain name configuration
    create_domain_name          = false
    domain_name                 = ""
    domain_name_certificate_arn = null
    create_domain_records       = false
    hosted_zone_name            = null

    # Stage configuration
    create_stage = true
    stage_name   = "$default"

    # Access logs configuration
    access_log_settings = {
      create_log_group            = false
      destination_arn             = null
      format                      = null
      log_group_name              = null
      log_group_retention_in_days = 30
      log_group_kms_key_id        = null
      log_group_skip_destroy      = null
      log_group_class             = null
      log_group_tags              = {}
    }

    # Default stage settings
    default_route_settings = {
      data_trace_enabled       = true
      detailed_metrics_enabled = true
      logging_level            = null
      throttling_burst_limit   = 500
      throttling_rate_limit    = 1000
    }

    # Authorizers configuration
    authorizers = {}

    # Routes configuration
    routes = {}

    # CORS configuration
    cors_configuration = null

    # Additional API Gateway configuration
    create_log_group      = true
    create_execution_role = true
  }

  # Create API Gateway flag is defined in api_gateway.tf

  # Final API Gateway configuration with individual variable overrides and global overrides
  api_gateway = merge(
    local.config.api_gateway,
    {
      enabled                 = var.create_api_gateway != null ? var.create_api_gateway : local.config.api_gateway.enabled
      include_kms_policy      = var.api_gateway_include_kms_policy != null ? var.api_gateway_include_kms_policy : local.config.api_gateway.include_kms_policy
      lambda_integration_type = var.api_gateway_lambda_integration_type != null ? var.api_gateway_lambda_integration_type : local.config.api_gateway.lambda_integration_type
      lambda_alias_name       = var.api_gateway_lambda_alias_name != null ? var.api_gateway_lambda_alias_name : local.config.api_gateway.lambda_alias_name
      lambda_version          = var.api_gateway_lambda_version != null ? var.api_gateway_lambda_version : local.config.api_gateway.lambda_version
      auto_set_lambda_uri     = var.api_gateway_auto_set_lambda_uri != null ? var.api_gateway_auto_set_lambda_uri : local.config.api_gateway.auto_set_lambda_uri

      # Apply global overrides for certificate, zone, and other settings
      domain_name_certificate_arn = var.certificate_arn != null ? var.certificate_arn : (var.api_gateway_domain_name_certificate_arn != null ? var.api_gateway_domain_name_certificate_arn : local.api_gateway_effective_certificate_arn)
      hosted_zone_name            = var.hosted_zone_name != null ? var.hosted_zone_name : (var.api_gateway_hosted_zone_name != null ? var.api_gateway_hosted_zone_name : local.api_gateway_effective_hosted_zone_name)

      # Other API Gateway specific settings
      name                   = var.api_gateway_name != null ? var.api_gateway_name : local.config.api_gateway.name
      description            = var.api_gateway_description != null ? var.api_gateway_description : local.config.api_gateway.description
      protocol_type          = var.api_gateway_protocol_type != null ? var.api_gateway_protocol_type : local.config.api_gateway.protocol_type
      create_domain_name     = var.api_gateway_create_domain_name != null ? var.api_gateway_create_domain_name : local.config.api_gateway.create_domain_name
      domain_name            = var.api_gateway_domain_name != null ? var.api_gateway_domain_name : local.config.api_gateway.domain_name
      create_domain_records  = var.api_gateway_create_domain_records != null ? var.api_gateway_create_domain_records : local.config.api_gateway.create_domain_records
      create_stage           = var.api_gateway_create_stage != null ? var.api_gateway_create_stage : local.config.api_gateway.create_stage
      stage_name             = var.api_gateway_stage_name != null ? var.api_gateway_stage_name : local.config.api_gateway.stage_name
      access_log_settings    = var.api_gateway_access_log_settings != null ? var.api_gateway_access_log_settings : local.config.api_gateway.access_log_settings
      default_route_settings = var.api_gateway_default_route_settings != null ? var.api_gateway_default_route_settings : local.config.api_gateway.default_route_settings
      authorizers            = var.api_gateway_authorizers != null ? var.api_gateway_authorizers : local.config.api_gateway.authorizers
      routes                 = var.api_gateway_routes != null ? var.api_gateway_routes : local.config.api_gateway.routes
      cors_configuration     = var.api_gateway_cors_configuration != null ? var.api_gateway_cors_configuration : local.config.api_gateway.cors_configuration
      create_log_group       = var.api_gateway_create_log_group != null ? var.api_gateway_create_log_group : local.config.api_gateway.create_log_group
      create_execution_role  = var.api_gateway_create_execution_role != null ? var.api_gateway_create_execution_role : local.config.api_gateway.create_execution_role
    }
  )
}
