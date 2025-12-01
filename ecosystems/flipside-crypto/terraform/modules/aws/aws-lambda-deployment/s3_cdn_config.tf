# S3 CDN Configuration Defaults
# This file defines the default configuration for S3 CDN

locals {
  # S3 CDN configuration defaults
  s3_cdn_defaults = {
    enabled = false

    # S3 CDN KMS Policy Configuration
    include_s3_kms_policy         = true
    include_cloudfront_kms_policy = true
    module_version                = "0.97.0"

    # Lambda@Edge Integration Configuration
    lambda_integration_type                = "function"
    lambda_alias_name                      = null
    lambda_version                         = null
    lambda_event_type                      = "origin-request"
    lambda_include_body                    = false
    additional_lambda_function_association = []

    # S3 Origin Configuration
    origin_bucket                      = null
    origin_path                        = ""
    origin_force_destroy               = false
    versioning_enabled                 = true
    encryption_enabled                 = true
    website_enabled                    = false
    s3_website_password_enabled        = false
    index_document                     = "index.html"
    error_document                     = ""
    redirect_all_requests_to           = ""
    routing_rules                      = ""
    cors_allowed_headers               = ["*"]
    cors_allowed_methods               = ["GET"]
    cors_allowed_origins               = []
    cors_expose_headers                = ["ETag"]
    cors_max_age_seconds               = 3600
    s3_object_ownership                = "ObjectWriter"
    block_origin_public_access_enabled = false

    # CloudFront Configuration
    acm_certificate_arn      = ""
    aliases                  = []
    external_aliases         = []
    dns_alias_enabled        = false
    parent_zone_id           = null
    parent_zone_name         = ""
    price_class              = "PriceClass_100"
    distribution_enabled     = true
    wait_for_deployment      = true
    default_root_object      = "index.html"
    comment                  = "Managed by Terraform"
    ipv6_enabled             = true
    http_version             = "http2"
    minimum_protocol_version = ""
    web_acl_id               = ""

    # Cache Configuration
    allowed_methods                   = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods                    = ["GET", "HEAD"]
    cache_policy_id                   = null
    origin_request_policy_id          = null
    response_headers_policy_id        = ""
    compress                          = true
    viewer_protocol_policy            = "redirect-to-https"
    default_ttl                       = 60
    min_ttl                           = 0
    max_ttl                           = 31536000
    trusted_signers                   = []
    trusted_key_groups                = []
    forward_query_string              = false
    query_string_cache_keys           = []
    forward_header_values             = ["Access-Control-Request-Headers", "Access-Control-Request-Method", "Origin"]
    forward_cookies                   = "none"
    forward_cookies_whitelisted_names = []

    # Geo Restriction
    geo_restriction_type      = "none"
    geo_restriction_locations = []

    # Logging Configuration
    cloudfront_access_logging_enabled     = true
    cloudfront_access_log_create_bucket   = true
    cloudfront_access_log_bucket_name     = ""
    cloudfront_access_log_prefix          = ""
    cloudfront_access_log_include_cookies = false
    s3_access_logging_enabled             = null
    s3_access_log_bucket_name             = ""
    s3_access_log_prefix                  = ""

    # Advanced Configuration
    additional_bucket_policy      = "{}"
    override_origin_bucket_policy = true
    bucket_versioning             = "Disabled"
    deployment_principal_arns     = {}
    deployment_actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:GetBucketLocation",
      "s3:AbortMultipartUpload"
    ]
    custom_error_response                     = []
    ordered_cache                             = []
    custom_origins                            = []
    s3_origins                                = []
    origin_groups                             = []
    custom_origin_headers                     = []
    origin_access_type                        = "origin_access_identity"
    origin_access_control_signing_behavior    = "always"
    cloudfront_origin_access_identity_path    = ""
    cloudfront_origin_access_identity_iam_arn = ""
    cloudfront_origin_access_control_id       = ""
    origin_shield_enabled                     = false
    origin_ssl_protocols                      = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    realtime_log_config_arn                   = null
    function_association                      = []
  }



  # Final S3 CDN configuration with individual variable overrides and global overrides
  s3_cdn = merge(
    local.config.s3_cdn,
    {
      enabled                                = var.create_s3_cdn != null ? var.create_s3_cdn : local.config.s3_cdn.enabled
      include_s3_kms_policy                  = var.s3_cdn_include_s3_kms_policy != null ? var.s3_cdn_include_s3_kms_policy : local.config.s3_cdn.include_s3_kms_policy
      include_cloudfront_kms_policy          = var.s3_cdn_include_cloudfront_kms_policy != null ? var.s3_cdn_include_cloudfront_kms_policy : local.config.s3_cdn.include_cloudfront_kms_policy
      module_version                         = var.s3_cdn_module_version != null ? var.s3_cdn_module_version : local.config.s3_cdn.module_version
      lambda_integration_type                = var.s3_cdn_lambda_integration_type != null ? var.s3_cdn_lambda_integration_type : local.config.s3_cdn.lambda_integration_type
      lambda_alias_name                      = var.s3_cdn_lambda_alias_name != null ? var.s3_cdn_lambda_alias_name : local.config.s3_cdn.lambda_alias_name
      lambda_version                         = var.s3_cdn_lambda_version != null ? var.s3_cdn_lambda_version : local.config.s3_cdn.lambda_version
      lambda_event_type                      = var.s3_cdn_lambda_event_type != null ? var.s3_cdn_lambda_event_type : local.config.s3_cdn.lambda_event_type
      lambda_include_body                    = var.s3_cdn_lambda_include_body != null ? var.s3_cdn_lambda_include_body : local.config.s3_cdn.lambda_include_body
      additional_lambda_function_association = var.s3_cdn_additional_lambda_function_association != null ? var.s3_cdn_additional_lambda_function_association : local.config.s3_cdn.additional_lambda_function_association

      # Apply global overrides for certificate, zone, and other settings
      acm_certificate_arn               = var.certificate_arn != null ? var.certificate_arn : (var.s3_cdn_acm_certificate_arn != null ? var.s3_cdn_acm_certificate_arn : local.s3_cdn_effective_certificate_arn)
      parent_zone_id                    = var.zone_id != null ? var.zone_id : (var.s3_cdn_parent_zone_id != null ? var.s3_cdn_parent_zone_id : local.s3_cdn_effective_zone_id)
      parent_zone_name                  = var.hosted_zone_name != null ? var.hosted_zone_name : (var.s3_cdn_parent_zone_name != null ? var.s3_cdn_parent_zone_name : local.s3_cdn_effective_zone_name)
      wait_for_deployment               = var.wait_for_deployment != null ? var.wait_for_deployment : (var.s3_cdn_wait_for_deployment != null ? var.s3_cdn_wait_for_deployment : local.s3_cdn_effective_wait_for_deployment)
      default_ttl                       = var.default_ttl != null ? var.default_ttl : (var.s3_cdn_default_ttl != null ? var.s3_cdn_default_ttl : local.s3_cdn_effective_default_ttl)
      min_ttl                           = var.min_ttl != null ? var.min_ttl : (var.s3_cdn_min_ttl != null ? var.s3_cdn_min_ttl : local.s3_cdn_effective_min_ttl)
      max_ttl                           = var.max_ttl != null ? var.max_ttl : (var.s3_cdn_max_ttl != null ? var.s3_cdn_max_ttl : local.s3_cdn_effective_max_ttl)
      cloudfront_access_logging_enabled = var.enable_access_logging != null ? var.enable_access_logging : (var.s3_cdn_cloudfront_access_logging_enabled != null ? var.s3_cdn_cloudfront_access_logging_enabled : local.s3_cdn_effective_access_logging_enabled)
      cloudfront_access_log_bucket_name = var.access_log_bucket_name != null ? var.access_log_bucket_name : (var.s3_cdn_cloudfront_access_log_bucket_name != null ? var.s3_cdn_cloudfront_access_log_bucket_name : local.s3_cdn_effective_access_log_bucket_name)

      # Other S3 CDN specific settings
      aliases                                = var.s3_cdn_aliases != null ? var.s3_cdn_aliases : local.config.s3_cdn.aliases
      external_aliases                       = var.s3_cdn_external_aliases != null ? var.s3_cdn_external_aliases : local.config.s3_cdn.external_aliases
      dns_alias_enabled                      = var.s3_cdn_dns_alias_enabled != null ? var.s3_cdn_dns_alias_enabled : local.config.s3_cdn.dns_alias_enabled
      price_class                            = var.s3_cdn_price_class != null ? var.s3_cdn_price_class : local.config.s3_cdn.price_class
      distribution_enabled                   = var.s3_cdn_distribution_enabled != null ? var.s3_cdn_distribution_enabled : local.config.s3_cdn.distribution_enabled
      default_root_object                    = var.s3_cdn_default_root_object != null ? var.s3_cdn_default_root_object : local.config.s3_cdn.default_root_object
      comment                                = var.s3_cdn_comment != null ? var.s3_cdn_comment : local.config.s3_cdn.comment
      ipv6_enabled                           = var.s3_cdn_ipv6_enabled != null ? var.s3_cdn_ipv6_enabled : local.config.s3_cdn.ipv6_enabled
      http_version                           = var.s3_cdn_http_version != null ? var.s3_cdn_http_version : local.config.s3_cdn.http_version
      minimum_protocol_version               = var.s3_cdn_minimum_protocol_version != null ? var.s3_cdn_minimum_protocol_version : local.config.s3_cdn.minimum_protocol_version
      web_acl_id                             = var.s3_cdn_web_acl_id != null ? var.s3_cdn_web_acl_id : local.config.s3_cdn.web_acl_id
      allowed_methods                        = var.s3_cdn_allowed_methods != null ? var.s3_cdn_allowed_methods : local.config.s3_cdn.allowed_methods
      cached_methods                         = var.s3_cdn_cached_methods != null ? var.s3_cdn_cached_methods : local.config.s3_cdn.cached_methods
      cache_policy_id                        = var.s3_cdn_cache_policy_id != null ? var.s3_cdn_cache_policy_id : local.config.s3_cdn.cache_policy_id
      origin_request_policy_id               = var.s3_cdn_origin_request_policy_id != null ? var.s3_cdn_origin_request_policy_id : local.config.s3_cdn.origin_request_policy_id
      response_headers_policy_id             = var.s3_cdn_response_headers_policy_id != null ? var.s3_cdn_response_headers_policy_id : local.config.s3_cdn.response_headers_policy_id
      compress                               = var.s3_cdn_compress != null ? var.s3_cdn_compress : local.config.s3_cdn.compress
      viewer_protocol_policy                 = var.s3_cdn_viewer_protocol_policy != null ? var.s3_cdn_viewer_protocol_policy : local.config.s3_cdn.viewer_protocol_policy
      trusted_signers                        = var.s3_cdn_trusted_signers != null ? var.s3_cdn_trusted_signers : local.config.s3_cdn.trusted_signers
      trusted_key_groups                     = var.s3_cdn_trusted_key_groups != null ? var.s3_cdn_trusted_key_groups : local.config.s3_cdn.trusted_key_groups
      forward_query_string                   = var.s3_cdn_forward_query_string != null ? var.s3_cdn_forward_query_string : local.config.s3_cdn.forward_query_string
      query_string_cache_keys                = var.s3_cdn_query_string_cache_keys != null ? var.s3_cdn_query_string_cache_keys : local.config.s3_cdn.query_string_cache_keys
      forward_header_values                  = var.s3_cdn_forward_header_values != null ? var.s3_cdn_forward_header_values : local.config.s3_cdn.forward_header_values
      forward_cookies                        = var.s3_cdn_forward_cookies != null ? var.s3_cdn_forward_cookies : local.config.s3_cdn.forward_cookies
      forward_cookies_whitelisted_names      = var.s3_cdn_forward_cookies_whitelisted_names != null ? var.s3_cdn_forward_cookies_whitelisted_names : local.config.s3_cdn.forward_cookies_whitelisted_names
      geo_restriction_type                   = var.s3_cdn_geo_restriction_type != null ? var.s3_cdn_geo_restriction_type : local.config.s3_cdn.geo_restriction_type
      geo_restriction_locations              = var.s3_cdn_geo_restriction_locations != null ? var.s3_cdn_geo_restriction_locations : local.config.s3_cdn.geo_restriction_locations
      cloudfront_access_log_create_bucket    = var.s3_cdn_cloudfront_access_log_create_bucket != null ? var.s3_cdn_cloudfront_access_log_create_bucket : local.config.s3_cdn.cloudfront_access_log_create_bucket
      cloudfront_access_log_prefix           = var.s3_cdn_cloudfront_access_log_prefix != null ? var.s3_cdn_cloudfront_access_log_prefix : local.config.s3_cdn.cloudfront_access_log_prefix
      cloudfront_access_log_include_cookies  = var.s3_cdn_cloudfront_access_log_include_cookies != null ? var.s3_cdn_cloudfront_access_log_include_cookies : local.config.s3_cdn.cloudfront_access_log_include_cookies
      s3_access_logging_enabled              = var.s3_cdn_s3_access_logging_enabled != null ? var.s3_cdn_s3_access_logging_enabled : local.config.s3_cdn.s3_access_logging_enabled
      s3_access_log_bucket_name              = var.s3_cdn_s3_access_log_bucket_name != null ? var.s3_cdn_s3_access_log_bucket_name : local.config.s3_cdn.s3_access_log_bucket_name
      s3_access_log_prefix                   = var.s3_cdn_s3_access_log_prefix != null ? var.s3_cdn_s3_access_log_prefix : local.config.s3_cdn.s3_access_log_prefix
      additional_bucket_policy               = var.s3_cdn_additional_bucket_policy != null ? var.s3_cdn_additional_bucket_policy : local.config.s3_cdn.additional_bucket_policy
      override_origin_bucket_policy          = var.s3_cdn_override_origin_bucket_policy != null ? var.s3_cdn_override_origin_bucket_policy : local.config.s3_cdn.override_origin_bucket_policy
      bucket_versioning                      = var.s3_cdn_bucket_versioning != null ? var.s3_cdn_bucket_versioning : local.config.s3_cdn.bucket_versioning
      deployment_principal_arns              = var.s3_cdn_deployment_principal_arns != null ? var.s3_cdn_deployment_principal_arns : local.config.s3_cdn.deployment_principal_arns
      deployment_actions                     = var.s3_cdn_deployment_actions != null ? var.s3_cdn_deployment_actions : local.config.s3_cdn.deployment_actions
      custom_error_response                  = var.s3_cdn_custom_error_response != null ? var.s3_cdn_custom_error_response : local.config.s3_cdn.custom_error_response
      ordered_cache                          = var.s3_cdn_ordered_cache != null ? var.s3_cdn_ordered_cache : local.config.s3_cdn.ordered_cache
      custom_origins                         = var.s3_cdn_custom_origins != null ? var.s3_cdn_custom_origins : local.config.s3_cdn.custom_origins
      s3_origins                             = var.s3_cdn_s3_origins != null ? var.s3_cdn_s3_origins : local.config.s3_cdn.s3_origins
      origin_groups                          = var.s3_cdn_origin_groups != null ? var.s3_cdn_origin_groups : local.config.s3_cdn.origin_groups
      custom_origin_headers                  = var.s3_cdn_custom_origin_headers != null ? var.s3_cdn_custom_origin_headers : local.config.s3_cdn.custom_origin_headers
      origin_access_type                     = var.s3_cdn_origin_access_type != null ? var.s3_cdn_origin_access_type : local.config.s3_cdn.origin_access_type
      origin_access_control_signing_behavior = var.s3_cdn_origin_access_control_signing_behavior != null ? var.s3_cdn_origin_access_control_signing_behavior : local.config.s3_cdn.origin_access_control_signing_behavior
      origin_shield_enabled                  = var.s3_cdn_origin_shield_enabled != null ? var.s3_cdn_origin_shield_enabled : local.config.s3_cdn.origin_shield_enabled
      origin_ssl_protocols                   = var.s3_cdn_origin_ssl_protocols != null ? var.s3_cdn_origin_ssl_protocols : local.config.s3_cdn.origin_ssl_protocols
      realtime_log_config_arn                = var.s3_cdn_realtime_log_config_arn != null ? var.s3_cdn_realtime_log_config_arn : local.config.s3_cdn.realtime_log_config_arn
      function_association                   = var.s3_cdn_function_association != null ? var.s3_cdn_function_association : local.config.s3_cdn.function_association
    }
  )
}
