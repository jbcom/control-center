# KMS Configuration Defaults
# This file defines the default configuration for KMS keys

locals {
  # KMS configuration defaults
  kms_defaults = {
    enabled                     = false
    create_key                  = false
    create_key_policy           = false
    key_name                    = null
    key_description             = null
    key_deletion_window_in_days = 30
    key_enable_key_rotation     = true
    key_aliases                 = []
    key_tags                    = {}

    # KMS Key Policy Variables
    lambda_include_kms_policy          = true
    key_include_lambda_policy          = true
    key_include_api_gateway_policy     = true
    key_include_s3_policy              = true
    key_include_cloudfront_policy      = true
    key_include_lambda_edge_policy     = true
    key_include_cloudwatch_logs_policy = true
    key_account_ids                    = []
    key_authorize_all_in_account       = true
  }

  # Create KMS key flag
  create_kms_key = var.create_kms_key != null ? var.create_kms_key : local.config.kms.enabled

  # Final KMS configuration with individual variable overrides and global overrides
  kms = merge(
    local.config.kms,
    {
      enabled                            = var.create_kms_key != null ? var.create_kms_key : local.config.kms.enabled
      create_key                         = var.create_kms_key != null ? var.create_kms_key : local.config.kms.create_key
      create_key_policy                  = var.create_kms_key_policy != null ? var.create_kms_key_policy : local.config.kms.create_key_policy
      key_name                           = var.kms_key_name != null ? var.kms_key_name : local.config.kms.key_name
      key_description                    = var.kms_key_description != null ? var.kms_key_description : local.config.kms.key_description
      key_deletion_window_in_days        = var.kms_key_deletion_window_in_days != null ? var.kms_key_deletion_window_in_days : local.config.kms.key_deletion_window_in_days
      key_enable_key_rotation            = var.kms_key_enable_key_rotation != null ? var.kms_key_enable_key_rotation : local.config.kms.key_enable_key_rotation
      key_aliases                        = var.kms_key_aliases != null ? var.kms_key_aliases : local.config.kms.key_aliases
      key_tags                           = var.kms_key_tags != null ? var.kms_key_tags : local.config.kms.key_tags
      lambda_include_kms_policy          = var.lambda_include_kms_policy != null ? var.lambda_include_kms_policy : local.config.kms.lambda_include_kms_policy
      key_include_lambda_policy          = var.kms_key_include_lambda_policy != null ? var.kms_key_include_lambda_policy : local.config.kms.key_include_lambda_policy
      key_include_api_gateway_policy     = var.kms_key_include_api_gateway_policy != null ? var.kms_key_include_api_gateway_policy : local.config.kms.key_include_api_gateway_policy
      key_include_s3_policy              = var.kms_key_include_s3_policy != null ? var.kms_key_include_s3_policy : local.config.kms.key_include_s3_policy
      key_include_cloudfront_policy      = var.kms_key_include_cloudfront_policy != null ? var.kms_key_include_cloudfront_policy : local.config.kms.key_include_cloudfront_policy
      key_include_lambda_edge_policy     = var.kms_key_include_lambda_edge_policy != null ? var.kms_key_include_lambda_edge_policy : local.config.kms.key_include_lambda_edge_policy
      key_include_cloudwatch_logs_policy = var.kms_key_include_cloudwatch_logs_policy != null ? var.kms_key_include_cloudwatch_logs_policy : local.config.kms.key_include_cloudwatch_logs_policy
      key_account_ids                    = var.kms_key_account_ids != null ? var.kms_key_account_ids : local.config.kms.key_account_ids
      key_authorize_all_in_account       = var.kms_key_authorize_all_in_account != null ? var.kms_key_authorize_all_in_account : local.config.kms.key_authorize_all_in_account
    }
  )
}
