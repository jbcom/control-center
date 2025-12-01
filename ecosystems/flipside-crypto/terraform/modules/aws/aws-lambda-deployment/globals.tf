# Global Variable Overrides
# This file contains logic to apply global variable overrides to component-specific variables

locals {
  # DNS Configuration
  effective_zone_id = var.zone_id

  # Certificate Configuration
  effective_certificate_arn = var.certificate_arn

  # KMS Configuration
  effective_kms_key_arn                = var.kms_key_arn != null ? var.kms_key_arn : (local.create_kms_key ? module.kms_key[0].arn : null)
  effective_cloudwatch_logs_kms_key_id = var.kms_key_arn != null ? var.kms_key_arn : (local.create_kms_key ? module.kms_key[0].arn : null)

  # Logging Configuration
  effective_cloudwatch_logs_retention_in_days = var.log_retention_days != null ? var.log_retention_days : var.cloudwatch_logs_retention_in_days
  effective_enable_access_logging             = var.enable_access_logging
  effective_access_log_bucket_name            = var.access_log_bucket_name

  # Deployment Configuration
  effective_wait_for_deployment = var.wait_for_deployment

  # Cache Configuration
  effective_default_ttl = var.default_ttl
  effective_min_ttl     = var.min_ttl
  effective_max_ttl     = var.max_ttl

  # API Gateway Overrides
  api_gateway_effective_certificate_arn  = var.certificate_arn != null ? var.certificate_arn : var.api_gateway_domain_name_certificate_arn
  api_gateway_effective_zone_id          = var.zone_id
  api_gateway_effective_hosted_zone_name = var.hosted_zone_name != null ? var.hosted_zone_name : var.api_gateway_hosted_zone_name

  # S3 CDN Overrides
  s3_cdn_effective_certificate_arn        = var.certificate_arn != null ? var.certificate_arn : var.s3_cdn_acm_certificate_arn
  s3_cdn_effective_zone_id                = var.zone_id != null ? var.zone_id : var.s3_cdn_parent_zone_id
  s3_cdn_effective_zone_name              = var.hosted_zone_name != null ? var.hosted_zone_name : var.s3_cdn_parent_zone_name
  s3_cdn_effective_wait_for_deployment    = var.wait_for_deployment != null ? var.wait_for_deployment : var.s3_cdn_wait_for_deployment
  s3_cdn_effective_default_ttl            = var.default_ttl != null ? var.default_ttl : var.s3_cdn_default_ttl
  s3_cdn_effective_min_ttl                = var.min_ttl != null ? var.min_ttl : var.s3_cdn_min_ttl
  s3_cdn_effective_max_ttl                = var.max_ttl != null ? var.max_ttl : var.s3_cdn_max_ttl
  s3_cdn_effective_access_logging_enabled = var.enable_access_logging != null ? var.enable_access_logging : var.s3_cdn_cloudfront_access_logging_enabled
  s3_cdn_effective_access_log_bucket_name = var.access_log_bucket_name != null ? var.access_log_bucket_name : var.s3_cdn_cloudfront_access_log_bucket_name
}
