# API Gateway Configuration Variables

variable "create_api_gateway" {
  type        = bool
  default     = false
  description = "Controls whether API Gateway resources should be created"
}

# API Gateway KMS Policy Configuration
variable "api_gateway_include_kms_policy" {
  type        = bool
  default     = true
  description = "Whether to include API Gateway in the KMS key policy"
  validation {
    condition     = !var.api_gateway_include_kms_policy || var.create_kms_key_policy
    error_message = "Cannot include API Gateway in KMS key policy when create_kms_key_policy is false."
  }
}

variable "api_gateway_lambda_integration_type" {
  type        = string
  default     = "function"
  description = "Type of Lambda integration to use. Valid values: 'function' (default Lambda function), 'alias' (Lambda alias), 'version' (specific Lambda version)"
}

variable "api_gateway_lambda_alias_name" {
  type        = string
  default     = null
  description = "Name of the Lambda alias to use for API Gateway integration. Required if api_gateway_lambda_integration_type is 'alias'"
}

variable "api_gateway_lambda_version" {
  type        = string
  default     = null
  description = "Version of the Lambda function to use for API Gateway integration. Required if api_gateway_lambda_integration_type is 'version'"
}

variable "api_gateway_auto_set_lambda_uri" {
  type        = bool
  default     = true
  description = "Whether to automatically set the Lambda function URI in route integrations if not specified"
}

variable "api_gateway_name" {
  type        = string
  default     = null
  description = "Name of the API Gateway. If not provided, will use the module name with context"
}

variable "api_gateway_description" {
  type        = string
  default     = null
  description = "Description of the API Gateway"
}

variable "api_gateway_protocol_type" {
  type        = string
  default     = "HTTP"
  description = "The API protocol. Valid values: HTTP, WEBSOCKET"
}

# Domain name configuration
variable "api_gateway_create_domain_name" {
  type        = bool
  default     = false
  description = "Whether to create API domain name resource"
}

variable "api_gateway_domain_name" {
  type        = string
  default     = ""
  description = "The domain name to use for API gateway"
}

variable "api_gateway_domain_name_certificate_arn" {
  type        = string
  default     = null
  description = "The ARN of an AWS-managed certificate that will be used by the endpoint for the domain name"
}

variable "api_gateway_create_domain_records" {
  type        = bool
  default     = false
  description = "Whether to create Route53 records for the domain name"
}

variable "api_gateway_hosted_zone_name" {
  type        = string
  default     = null
  description = "Optional domain name of the Hosted Zone where the domain should be created"
}

# Stage configuration
variable "api_gateway_create_stage" {
  type        = bool
  default     = true
  description = "Whether to create default stage"
}

variable "api_gateway_stage_name" {
  type        = string
  default     = "$default"
  description = "The name of the stage. Must be between 1 and 128 characters in length"
}

# Access logs configuration
variable "api_gateway_access_log_settings" {
  type = object({
    create_log_group            = optional(bool, false)
    destination_arn             = optional(string)
    format                      = optional(string)
    log_group_name              = optional(string)
    log_group_retention_in_days = optional(number, 30)
    log_group_kms_key_id        = optional(string)
    log_group_skip_destroy      = optional(bool)
    log_group_class             = optional(string)
    log_group_tags              = optional(map(string), {})
  })
  default     = {}
  description = "Settings for logging access in this stage"
}

# Default stage settings
variable "api_gateway_default_route_settings" {
  type = object({
    data_trace_enabled       = optional(bool, true)
    detailed_metrics_enabled = optional(bool, true)
    logging_level            = optional(string)
    throttling_burst_limit   = optional(number, 500)
    throttling_rate_limit    = optional(number, 1000)
  })
  default     = {}
  description = "The default route settings for the stage"
}

# Authorizers configuration
variable "api_gateway_authorizers" {
  type = map(object({
    authorizer_credentials_arn        = optional(string)
    authorizer_payload_format_version = optional(string)
    authorizer_result_ttl_in_seconds  = optional(number)
    authorizer_type                   = optional(string, "REQUEST")
    authorizer_uri                    = optional(string)
    enable_simple_responses           = optional(bool)
    identity_sources                  = optional(list(string))
    jwt_configuration = optional(object({
      audience = optional(list(string))
      issuer   = optional(string)
    }))
    name = optional(string)
  }))
  default     = {}
  description = "Map of API gateway authorizers to create"
}

# Routes configuration
variable "api_gateway_routes" {
  type = map(object({
    # Route
    authorizer_key             = optional(string)
    api_key_required           = optional(bool)
    authorization_scopes       = optional(list(string), [])
    authorization_type         = optional(string)
    authorizer_id              = optional(string)
    model_selection_expression = optional(string)
    operation_name             = optional(string)
    request_models             = optional(map(string), {})
    request_parameter = optional(object({
      request_parameter_key = optional(string)
      required              = optional(bool, false)
    }), {})
    route_response_selection_expression = optional(string)

    # Route settings
    data_trace_enabled       = optional(bool)
    detailed_metrics_enabled = optional(bool)
    logging_level            = optional(string)
    throttling_burst_limit   = optional(number)
    throttling_rate_limit    = optional(number)

    # Stage - Route response
    route_response = optional(object({
      create                     = optional(bool, false)
      model_selection_expression = optional(string)
      response_models            = optional(map(string))
      route_response_key         = optional(string, "$default")
    }), {})

    # Integration
    integration = object({
      connection_id             = optional(string)
      vpc_link_key              = optional(string)
      connection_type           = optional(string)
      content_handling_strategy = optional(string)
      credentials_arn           = optional(string)
      description               = optional(string)
      method                    = optional(string)
      subtype                   = optional(string)
      type                      = optional(string, "AWS_PROXY")
      uri                       = optional(string)
      passthrough_behavior      = optional(string)
      payload_format_version    = optional(string, "2.0")
      request_parameters        = optional(map(string), {})
      request_templates         = optional(map(string), {})
      response_parameters = optional(list(object({
        mappings    = map(string)
        status_code = string
      })))
      template_selection_expression = optional(string)
      timeout_milliseconds          = optional(number, 12000)
      tls_config = optional(object({
        server_name_to_verify = optional(string)
      }))

      # Integration Response
      response = optional(object({
        content_handling_strategy     = optional(string)
        integration_response_key      = optional(string)
        response_templates            = optional(map(string))
        template_selection_expression = optional(string)
      }), {})
    })
  }))
  default     = {}
  description = "Map of API gateway routes with integrations"
}

# CORS configuration
variable "api_gateway_cors_configuration" {
  type = object({
    allow_credentials = optional(bool)
    allow_headers     = optional(list(string))
    allow_methods     = optional(list(string))
    allow_origins     = optional(list(string))
    expose_headers    = optional(list(string), [])
    max_age           = optional(number)
  })
  default     = null
  description = "The cross-origin resource sharing (CORS) configuration. Applicable for HTTP APIs"
}

# Additional API Gateway configuration
variable "api_gateway_create_log_group" {
  type        = bool
  default     = true
  description = "Controls whether CloudWatch Log Group for API Gateway should be created"
}

variable "api_gateway_create_execution_role" {
  type        = bool
  default     = true
  description = "Controls whether IAM role for API Gateway execution should be created"
}
