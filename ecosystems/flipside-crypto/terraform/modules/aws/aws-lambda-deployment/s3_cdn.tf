# CloudFront S3 CDN with Lambda@Edge integration
# This file adds CloudFront S3 CDN support to the aws-lambda-deployment module

locals {
  create_s3_cdn = var.create_s3_cdn && module.this.enabled

  # Determine the Lambda function ARN based on the integration type
  lambda_function_arn = local.create_s3_cdn ? (
    var.s3_cdn_lambda_integration_type == "function" ? aws_lambda_function.this[0].arn : (
      var.s3_cdn_lambda_integration_type == "alias" ? (
        var.create_alias && var.s3_cdn_lambda_alias_name != null ?
        "${aws_lambda_function.this[0].arn}:${var.s3_cdn_lambda_alias_name}" :
        aws_lambda_function.this[0].arn
        ) : (
        var.s3_cdn_lambda_integration_type == "version" && var.s3_cdn_lambda_version != null ?
        "${aws_lambda_function.this[0].arn}:${var.s3_cdn_lambda_version}" :
        aws_lambda_function.this[0].arn
      )
    )
  ) : null

  # Determine the Lambda function qualifier based on the integration type
  s3_cdn_lambda_function_qualifier = local.create_s3_cdn ? (
    var.s3_cdn_lambda_integration_type == "function" ? null : (
      var.s3_cdn_lambda_integration_type == "alias" ? (
        var.create_alias && var.s3_cdn_lambda_alias_name != null ?
        var.s3_cdn_lambda_alias_name : null
        ) : (
        var.s3_cdn_lambda_integration_type == "version" && var.s3_cdn_lambda_version != null ?
        var.s3_cdn_lambda_version : null
      )
    )
  ) : null

  # Create the Lambda@Edge function association based on the provided configuration
  lambda_edge_function_association = local.create_s3_cdn ? [
    {
      event_type   = var.s3_cdn_lambda_event_type
      include_body = var.s3_cdn_lambda_include_body
      lambda_arn   = local.lambda_function_arn
    }
  ] : []
}

# CloudFront S3 CDN with Lambda@Edge integration
module "cloudfront_s3_cdn" {
  source  = "cloudposse/cloudfront-s3-cdn/aws"
  version = "1.1.0" # Using latest available version

  count = local.create_s3_cdn ? 1 : 0

  # Context
  namespace   = module.this.namespace
  environment = module.this.environment
  stage       = module.this.stage
  name        = module.this.name
  attributes  = module.this.attributes
  tags        = module.this.tags

  # S3 Origin Configuration
  origin_bucket                      = var.s3_cdn_origin_bucket
  origin_path                        = var.s3_cdn_origin_path
  origin_force_destroy               = var.s3_cdn_origin_force_destroy
  versioning_enabled                 = var.s3_cdn_versioning_enabled
  encryption_enabled                 = var.s3_cdn_encryption_enabled
  website_enabled                    = var.s3_cdn_website_enabled
  s3_website_password_enabled        = var.s3_cdn_s3_website_password_enabled
  index_document                     = var.s3_cdn_index_document
  error_document                     = var.s3_cdn_error_document
  redirect_all_requests_to           = var.s3_cdn_redirect_all_requests_to
  routing_rules                      = var.s3_cdn_routing_rules
  cors_allowed_headers               = var.s3_cdn_cors_allowed_headers
  cors_allowed_methods               = var.s3_cdn_cors_allowed_methods
  cors_allowed_origins               = var.s3_cdn_cors_allowed_origins
  cors_expose_headers                = var.s3_cdn_cors_expose_headers
  cors_max_age_seconds               = var.s3_cdn_cors_max_age_seconds
  s3_object_ownership                = var.s3_cdn_s3_object_ownership
  block_origin_public_access_enabled = var.s3_cdn_block_origin_public_access_enabled

  # CloudFront Configuration
  acm_certificate_arn      = local.s3_cdn_effective_certificate_arn
  aliases                  = var.s3_cdn_aliases
  external_aliases         = var.s3_cdn_external_aliases
  dns_alias_enabled        = var.s3_cdn_dns_alias_enabled
  parent_zone_id           = local.s3_cdn_effective_zone_id
  parent_zone_name         = local.s3_cdn_effective_zone_name
  price_class              = var.s3_cdn_price_class
  distribution_enabled     = var.s3_cdn_distribution_enabled
  wait_for_deployment      = local.s3_cdn_effective_wait_for_deployment
  default_root_object      = var.s3_cdn_default_root_object
  comment                  = var.s3_cdn_comment
  ipv6_enabled             = var.s3_cdn_ipv6_enabled
  http_version             = var.s3_cdn_http_version
  minimum_protocol_version = var.s3_cdn_minimum_protocol_version
  web_acl_id               = var.s3_cdn_web_acl_id

  # Cache Configuration
  allowed_methods            = var.s3_cdn_allowed_methods
  cached_methods             = var.s3_cdn_cached_methods
  cache_policy_id            = var.s3_cdn_cache_policy_id
  origin_request_policy_id   = var.s3_cdn_origin_request_policy_id
  response_headers_policy_id = var.s3_cdn_response_headers_policy_id
  compress                   = var.s3_cdn_compress
  viewer_protocol_policy     = var.s3_cdn_viewer_protocol_policy
  default_ttl                = local.s3_cdn_effective_default_ttl
  min_ttl                    = local.s3_cdn_effective_min_ttl
  max_ttl                    = local.s3_cdn_effective_max_ttl
  trusted_signers            = var.s3_cdn_trusted_signers
  trusted_key_groups         = var.s3_cdn_trusted_key_groups
  forward_query_string       = var.s3_cdn_forward_query_string
  query_string_cache_keys    = var.s3_cdn_query_string_cache_keys
  forward_header_values      = var.s3_cdn_forward_header_values
  forward_cookies            = var.s3_cdn_forward_cookies
  # forward_cookies_whitelisted_names is not supported at the top level
  # It should be included in the ordered_cache parameter if needed

  # Geo Restriction
  geo_restriction_type      = var.s3_cdn_geo_restriction_type
  geo_restriction_locations = var.s3_cdn_geo_restriction_locations

  # Logging Configuration
  cloudfront_access_logging_enabled     = local.s3_cdn_effective_access_logging_enabled
  cloudfront_access_log_create_bucket   = var.s3_cdn_cloudfront_access_log_create_bucket
  cloudfront_access_log_bucket_name     = local.s3_cdn_effective_access_log_bucket_name
  cloudfront_access_log_prefix          = var.s3_cdn_cloudfront_access_log_prefix
  cloudfront_access_log_include_cookies = var.s3_cdn_cloudfront_access_log_include_cookies
  s3_access_logging_enabled             = var.s3_cdn_s3_access_logging_enabled
  s3_access_log_bucket_name             = var.s3_cdn_s3_access_log_bucket_name
  s3_access_log_prefix                  = var.s3_cdn_s3_access_log_prefix

  # Advanced Configuration
  additional_bucket_policy                  = var.s3_cdn_additional_bucket_policy
  override_origin_bucket_policy             = var.s3_cdn_override_origin_bucket_policy
  bucket_versioning                         = var.s3_cdn_bucket_versioning
  deployment_principal_arns                 = var.s3_cdn_deployment_principal_arns
  deployment_actions                        = var.s3_cdn_deployment_actions
  custom_error_response                     = var.s3_cdn_custom_error_response
  ordered_cache                             = var.s3_cdn_ordered_cache
  custom_origins                            = var.s3_cdn_custom_origins
  s3_origins                                = var.s3_cdn_s3_origins
  origin_groups                             = var.s3_cdn_origin_groups
  custom_origin_headers                     = var.s3_cdn_custom_origin_headers
  origin_access_type                        = var.s3_cdn_origin_access_type
  origin_access_control_signing_behavior    = var.s3_cdn_origin_access_control_signing_behavior
  cloudfront_origin_access_identity_path    = var.s3_cdn_cloudfront_origin_access_identity_path
  cloudfront_origin_access_identity_iam_arn = var.s3_cdn_cloudfront_origin_access_identity_iam_arn
  cloudfront_origin_access_control_id       = var.s3_cdn_cloudfront_origin_access_control_id
  origin_shield_enabled                     = var.s3_cdn_origin_shield_enabled
  origin_ssl_protocols                      = var.s3_cdn_origin_ssl_protocols
  realtime_log_config_arn                   = var.s3_cdn_realtime_log_config_arn
  function_association                      = var.s3_cdn_function_association

  # Lambda@Edge Configuration
  lambda_function_association = concat(local.lambda_edge_function_association, var.s3_cdn_additional_lambda_function_association)
}

# Lambda permission for CloudFront to invoke the Lambda@Edge function
resource "aws_lambda_permission" "cloudfront_lambda_edge" {
  count = local.create_s3_cdn ? 1 : 0

  statement_id  = "AllowExecutionFromCloudFront"
  action        = "lambda:GetFunction"
  function_name = aws_lambda_function.this[0].function_name
  qualifier     = local.s3_cdn_lambda_function_qualifier
  principal     = "edgelambda.amazonaws.com"
}

# Additional Lambda permission for CloudFront to invoke the Lambda@Edge function
resource "aws_lambda_permission" "cloudfront_lambda_edge_invoke" {
  count = local.create_s3_cdn ? 1 : 0

  statement_id  = "AllowInvokeFromCloudFront"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this[0].function_name
  qualifier     = local.s3_cdn_lambda_function_qualifier
  principal     = "edgelambda.amazonaws.com"
}
