# Main Configuration Structure for aws-lambda-deployment module
# This file defines the top-level config variable and imports component-specific defaults

variable "config" {
  type = any
  default = {
    # Core configuration
    enabled = true

    # Component configurations are imported from their respective files
    lambda      = {}
    kms         = {}
    s3_cdn      = {}
    api_gateway = {}
    dns         = {}
  }
  description = <<-EOT
    Single object for setting entire configuration at once.
    See description of individual variables for details.
    Leave string and numeric variables as `null` to use default value.
    Individual variable settings (non-null) override settings in config object.
  EOT
}

# Import component-specific defaults and merge with user-provided config
locals {
  # User-provided config or empty map if not provided
  user_config = var.config != null ? var.config : {}

  # Merge user config with component defaults
  config = {
    enabled     = try(local.user_config.enabled, true)
    lambda      = merge(local.lambda_defaults, try(local.user_config.lambda, {}))
    kms         = merge(local.kms_defaults, try(local.user_config.kms, {}))
    s3_cdn      = merge(local.s3_cdn_defaults, try(local.user_config.s3_cdn, {}))
    api_gateway = merge(local.api_gateway_defaults, try(local.user_config.api_gateway, {}))
    dns         = merge(local.dns_defaults, try(local.user_config.dns, {}))
  }
}
