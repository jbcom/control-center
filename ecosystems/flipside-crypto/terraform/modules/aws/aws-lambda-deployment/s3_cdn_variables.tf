# S3 CDN Configuration Variables

variable "create_s3_cdn" {
  type        = bool
  default     = false
  description = "Controls whether CloudFront S3 CDN resources should be created"
}

# S3 CDN KMS Policy Configuration
variable "s3_cdn_include_s3_kms_policy" {
  type        = bool
  default     = true
  description = "Whether to include S3 in the KMS key policy"
  validation {
    condition     = !var.s3_cdn_include_s3_kms_policy || var.create_kms_key_policy
    error_message = "Cannot include S3 in KMS key policy when create_kms_key_policy is false."
  }
}

variable "s3_cdn_include_cloudfront_kms_policy" {
  type        = bool
  default     = true
  description = "Whether to include CloudFront in the KMS key policy"
  validation {
    condition     = !var.s3_cdn_include_cloudfront_kms_policy || var.create_kms_key_policy
    error_message = "Cannot include CloudFront in KMS key policy when create_kms_key_policy is false."
  }
}

variable "s3_cdn_module_version" {
  type        = string
  default     = "0.97.0"
  description = "Version of the cloudposse/cloudfront-s3-cdn/aws module to use"
}

# Lambda@Edge Integration Configuration
variable "s3_cdn_lambda_integration_type" {
  type        = string
  default     = "function"
  description = "Type of Lambda integration to use with CloudFront. Valid values: 'function' (default Lambda function), 'alias' (Lambda alias), 'version' (specific Lambda version)"
}

variable "s3_cdn_lambda_alias_name" {
  type        = string
  default     = null
  description = "Name of the Lambda alias to use for CloudFront integration. Required if s3_cdn_lambda_integration_type is 'alias'"
}

variable "s3_cdn_lambda_version" {
  type        = string
  default     = null
  description = "Version of the Lambda function to use for CloudFront integration. Required if s3_cdn_lambda_integration_type is 'version'"
}

variable "s3_cdn_lambda_event_type" {
  type        = string
  default     = "origin-request"
  description = "The specific event to trigger the Lambda@Edge function. Valid values: viewer-request, origin-request, viewer-response, origin-response"
}

variable "s3_cdn_lambda_include_body" {
  type        = bool
  default     = false
  description = "When true, the request body is exposed to the Lambda@Edge function"
}

variable "s3_cdn_additional_lambda_function_association" {
  type = list(object({
    event_type   = string
    include_body = bool
    lambda_arn   = string
  }))
  default     = []
  description = "Additional Lambda@Edge functions to associate with the CloudFront distribution"
}

# S3 Origin Configuration
variable "s3_cdn_origin_bucket" {
  type        = string
  default     = null
  description = "Name of an existing S3 bucket to use as the origin. If not provided, a new bucket will be created"
}

variable "s3_cdn_origin_path" {
  type        = string
  default     = ""
  description = "An optional path that CloudFront appends to the origin domain name when requesting content"
}

variable "s3_cdn_origin_force_destroy" {
  type        = bool
  default     = false
  description = "Delete all objects from the bucket so that the bucket can be destroyed without error"
}

variable "s3_cdn_versioning_enabled" {
  type        = bool
  default     = true
  description = "When set to 'true' the S3 origin bucket will have versioning enabled"
}

variable "s3_cdn_encryption_enabled" {
  type        = bool
  default     = true
  description = "When set to 'true' the resource will have AES256 encryption enabled by default"
}

variable "s3_cdn_website_enabled" {
  type        = bool
  default     = false
  description = "Set to true to enable the S3 bucket to serve as a website independently of CloudFront"
}

variable "s3_cdn_s3_website_password_enabled" {
  type        = bool
  default     = false
  description = "If set to true, and website_enabled is also true, a password will be required in the Referrer field of the HTTP request to access the website"
}

variable "s3_cdn_index_document" {
  type        = string
  default     = "index.html"
  description = "Amazon S3 returns this index document when requests are made to the root domain or any of the subfolders"
}

variable "s3_cdn_error_document" {
  type        = string
  default     = ""
  description = "An absolute path to the document to return in case of a 4XX error"
}

variable "s3_cdn_redirect_all_requests_to" {
  type        = string
  default     = ""
  description = "A hostname to redirect all website requests for this distribution to"
}

variable "s3_cdn_routing_rules" {
  type        = string
  default     = ""
  description = "A JSON array containing routing rules describing redirect behavior and when redirects are applied"
}

variable "s3_cdn_cors_allowed_headers" {
  type        = list(string)
  default     = ["*"]
  description = "List of allowed headers for S3 bucket CORS configuration"
}

variable "s3_cdn_cors_allowed_methods" {
  type        = list(string)
  default     = ["GET"]
  description = "List of allowed methods for S3 bucket CORS configuration"
}

variable "s3_cdn_cors_allowed_origins" {
  type        = list(string)
  default     = []
  description = "List of allowed origins for S3 bucket CORS configuration"
}

variable "s3_cdn_cors_expose_headers" {
  type        = list(string)
  default     = ["ETag"]
  description = "List of expose header in the response for S3 bucket CORS configuration"
}

variable "s3_cdn_cors_max_age_seconds" {
  type        = number
  default     = 3600
  description = "Time in seconds that browser can cache the response for S3 bucket CORS configuration"
}

variable "s3_cdn_s3_object_ownership" {
  type        = string
  default     = "ObjectWriter"
  description = "Specifies the S3 object ownership control on the origin bucket. Valid values are ObjectWriter, BucketOwnerPreferred, and BucketOwnerEnforced"
}

variable "s3_cdn_block_origin_public_access_enabled" {
  type        = bool
  default     = false
  description = "When set to 'true' the S3 origin bucket will have public access block enabled"
}

# CloudFront Configuration
variable "s3_cdn_acm_certificate_arn" {
  type        = string
  default     = ""
  description = "Existing ACM Certificate ARN for the CloudFront distribution"
}

variable "s3_cdn_aliases" {
  type        = list(string)
  default     = []
  description = "List of FQDN's - Used to set the Alternate Domain Names (CNAMEs) setting on CloudFront"
}

variable "s3_cdn_external_aliases" {
  type        = list(string)
  default     = []
  description = "List of FQDN's - Used to set the Alternate Domain Names (CNAMEs) setting on CloudFront. No new route53 records will be created for these"
}

variable "s3_cdn_dns_alias_enabled" {
  type        = bool
  default     = false
  description = "Create a DNS alias for the CDN. Requires parent_zone_id or parent_zone_name"
}

variable "s3_cdn_parent_zone_id" {
  type        = string
  default     = null
  description = "ID of the hosted zone to contain the DNS record for the CDN"
}

variable "s3_cdn_parent_zone_name" {
  type        = string
  default     = ""
  description = "Name of the hosted zone to contain the DNS record for the CDN"
}

variable "s3_cdn_price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "Price class for this distribution: PriceClass_All, PriceClass_200, PriceClass_100"
}

variable "s3_cdn_distribution_enabled" {
  type        = bool
  default     = true
  description = "Set to false to create the distribution but still prevent CloudFront from serving requests"
}

variable "s3_cdn_wait_for_deployment" {
  type        = bool
  default     = true
  description = "When set to 'true' the resource will wait for the distribution status to change from InProgress to Deployed"
}

variable "s3_cdn_default_root_object" {
  type        = string
  default     = "index.html"
  description = "Object that CloudFront return when requests the root URL"
}

variable "s3_cdn_comment" {
  type        = string
  default     = "Managed by Terraform"
  description = "Comment for the CloudFront distribution"
}

variable "s3_cdn_ipv6_enabled" {
  type        = bool
  default     = true
  description = "Set to true to enable an AAAA DNS record to be set as well as the A record"
}

variable "s3_cdn_http_version" {
  type        = string
  default     = "http2"
  description = "The maximum HTTP version to support on the distribution. Allowed values are http1.1, http2, http2and3 and http3"
}

variable "s3_cdn_minimum_protocol_version" {
  type        = string
  default     = ""
  description = "Cloudfront TLS minimum protocol version"
}

variable "s3_cdn_web_acl_id" {
  type        = string
  default     = ""
  description = "ID of the AWS WAF web ACL that is associated with the distribution"
}

# Cache Configuration
variable "s3_cdn_allowed_methods" {
  type        = list(string)
  default     = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
  description = "List of allowed methods for CloudFront"
}

variable "s3_cdn_cached_methods" {
  type        = list(string)
  default     = ["GET", "HEAD"]
  description = "List of cached methods for CloudFront"
}

variable "s3_cdn_cache_policy_id" {
  type        = string
  default     = null
  description = "The unique identifier of the existing cache policy to attach to the default cache behavior"
}

variable "s3_cdn_origin_request_policy_id" {
  type        = string
  default     = null
  description = "The unique identifier of the origin request policy that is attached to the behavior"
}

variable "s3_cdn_response_headers_policy_id" {
  type        = string
  default     = ""
  description = "The identifier for a response headers policy"
}

variable "s3_cdn_compress" {
  type        = bool
  default     = true
  description = "Compress content for web requests that include Accept-Encoding: gzip in the request header"
}

variable "s3_cdn_viewer_protocol_policy" {
  type        = string
  default     = "redirect-to-https"
  description = "Limit the protocol users can use to access content. One of allow-all, https-only, or redirect-to-https"
}

variable "s3_cdn_default_ttl" {
  type        = number
  default     = 60
  description = "Default amount of time (in seconds) that an object is in a CloudFront cache"
}

variable "s3_cdn_min_ttl" {
  type        = number
  default     = 0
  description = "Minimum amount of time that you want objects to stay in CloudFront caches"
}

variable "s3_cdn_max_ttl" {
  type        = number
  default     = 31536000
  description = "Maximum amount of time (in seconds) that an object is in a CloudFront cache"
}

variable "s3_cdn_trusted_signers" {
  type        = list(string)
  default     = []
  description = "The AWS accounts, if any, that you want to allow to create signed URLs for private content"
}

variable "s3_cdn_trusted_key_groups" {
  type        = list(string)
  default     = []
  description = "A list of key group IDs that CloudFront can use to validate signed URLs or signed cookies"
}

variable "s3_cdn_forward_query_string" {
  type        = bool
  default     = false
  description = "Forward query strings to the origin that is associated with this cache behavior"
}

variable "s3_cdn_query_string_cache_keys" {
  type        = list(string)
  default     = []
  description = "When forward_query_string is enabled, only the query string keys listed in this argument are cached"
}

variable "s3_cdn_forward_header_values" {
  type        = list(string)
  default     = ["Access-Control-Request-Headers", "Access-Control-Request-Method", "Origin"]
  description = "A list of whitelisted header values to forward to the origin"
}

variable "s3_cdn_forward_cookies" {
  type        = string
  default     = "none"
  description = "Specifies whether you want CloudFront to forward all or no cookies to the origin. Can be 'all' or 'none'"
}

variable "s3_cdn_forward_cookies_whitelisted_names" {
  type        = list(string)
  default     = []
  description = "List of forwarded cookie names when forward_cookies is 'whitelist'"
}

# Geo Restriction
variable "s3_cdn_geo_restriction_type" {
  type        = string
  default     = "none"
  description = "Method that use to restrict distribution of your content by country: none, whitelist, or blacklist"
}

variable "s3_cdn_geo_restriction_locations" {
  type        = list(string)
  default     = []
  description = "List of country codes for which CloudFront either to distribute content (whitelist) or not distribute your content (blacklist)"
}

# Logging Configuration
variable "s3_cdn_cloudfront_access_logging_enabled" {
  type        = bool
  default     = true
  description = "Set true to enable delivery of CloudFront Access Logs to an S3 bucket"
}

variable "s3_cdn_cloudfront_access_log_create_bucket" {
  type        = bool
  default     = true
  description = "When true and cloudfront_access_logging_enabled is also true, this module will create a new, separate S3 bucket to receive CloudFront Access Logs"
}

variable "s3_cdn_cloudfront_access_log_bucket_name" {
  type        = string
  default     = ""
  description = "When cloudfront_access_log_create_bucket is false, this is the name of the existing S3 Bucket where CloudFront Access Logs are to be delivered"
}

variable "s3_cdn_cloudfront_access_log_prefix" {
  type        = string
  default     = ""
  description = "Prefix to use for CloudFront Access Log object keys"
}

variable "s3_cdn_cloudfront_access_log_include_cookies" {
  type        = bool
  default     = false
  description = "Set true to include cookies in CloudFront Access Logs"
}

variable "s3_cdn_s3_access_logging_enabled" {
  type        = bool
  default     = null
  description = "Set true to deliver S3 Access Logs to the s3_access_log_bucket_name bucket"
}

variable "s3_cdn_s3_access_log_bucket_name" {
  type        = string
  default     = ""
  description = "Name of the existing S3 bucket where S3 Access Logs will be delivered"
}

variable "s3_cdn_s3_access_log_prefix" {
  type        = string
  default     = ""
  description = "Prefix to use for S3 Access Log object keys"
}

# Advanced Configuration
variable "s3_cdn_additional_bucket_policy" {
  type        = string
  default     = "{}"
  description = "Additional policies for the bucket. If included in the policies, the variables $bucket_name, $origin_path and $cloudfront_origin_access_identity_iam_arn will be substituted"
}

variable "s3_cdn_override_origin_bucket_policy" {
  type        = bool
  default     = true
  description = "When using an existing origin bucket, setting this to 'false' will make it so the existing bucket policy will not be overriden"
}

variable "s3_cdn_bucket_versioning" {
  type        = string
  default     = "Disabled"
  description = "State of bucket versioning option"
}

variable "s3_cdn_deployment_principal_arns" {
  type        = map(list(string))
  default     = {}
  description = "Map of IAM Principal ARNs to lists of S3 path prefixes to grant deployment_actions permissions"
}

variable "s3_cdn_deployment_actions" {
  type        = list(string)
  default     = ["s3:PutObject", "s3:PutObjectAcl", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket", "s3:ListBucketMultipartUploads", "s3:GetBucketLocation", "s3:AbortMultipartUpload"]
  description = "List of actions to permit deployment_principal_arns to perform on bucket and bucket prefixes"
}

variable "s3_cdn_custom_error_response" {
  type = list(object({
    error_caching_min_ttl = string
    error_code            = string
    response_code         = string
    response_page_path    = string
  }))
  default     = []
  description = "List of one or more custom error response element maps"
}

variable "s3_cdn_ordered_cache" {
  type = list(object({
    target_origin_id = string
    path_pattern     = string

    allowed_methods    = list(string)
    cached_methods     = list(string)
    compress           = bool
    trusted_signers    = list(string)
    trusted_key_groups = list(string)

    cache_policy_id          = string
    origin_request_policy_id = string
    realtime_log_config_arn  = optional(string)

    viewer_protocol_policy     = string
    min_ttl                    = number
    default_ttl                = number
    max_ttl                    = number
    response_headers_policy_id = string

    forward_query_string              = bool
    forward_header_values             = list(string)
    forward_cookies                   = string
    forward_cookies_whitelisted_names = list(string)

    lambda_function_association = list(object({
      event_type   = string
      include_body = bool
      lambda_arn   = string
    }))

    function_association = list(object({
      event_type   = string
      function_arn = string
    }))
  }))
  default     = []
  description = "An ordered list of cache behaviors resource for this distribution"
}

variable "s3_cdn_custom_origins" {
  type = list(object({
    domain_name              = string
    origin_id                = string
    origin_path              = string
    origin_access_control_id = optional(string)
    custom_headers = list(object({
      name  = string
      value = string
    }))
    custom_origin_config = object({
      http_port                = number
      https_port               = number
      origin_protocol_policy   = string
      origin_ssl_protocols     = list(string)
      origin_keepalive_timeout = number
      origin_read_timeout      = number
    })
  }))
  default     = []
  description = "A list of additional custom website origins for this distribution"
}

variable "s3_cdn_s3_origins" {
  type = list(object({
    domain_name              = string
    origin_id                = string
    origin_path              = string
    origin_access_control_id = string
    s3_origin_config = object({
      origin_access_identity = string
    })
  }))
  default     = []
  description = "A list of S3 origins for this distribution"
}

variable "s3_cdn_origin_groups" {
  type = list(object({
    primary_origin_id  = string
    failover_origin_id = string
    failover_criteria  = list(string)
  }))
  default     = []
  description = "List of Origin Groups to create in the distribution"
}

variable "s3_cdn_custom_origin_headers" {
  type        = list(object({ name = string, value = string }))
  default     = []
  description = "A list of origin header parameters that will be sent to origin"
}

variable "s3_cdn_origin_access_type" {
  type        = string
  default     = "origin_access_identity"
  description = "Choose to use origin_access_control or orgin_access_identity"
}

variable "s3_cdn_origin_access_control_signing_behavior" {
  type        = string
  default     = "always"
  description = "Specifies which requests CloudFront signs. Specify always for the most common use case. Allowed values: always, never, and no-override"
}

variable "s3_cdn_cloudfront_origin_access_identity_path" {
  type        = string
  default     = ""
  description = "Existing cloudfront origin access identity path used in the cloudfront distribution's s3_origin_config content"
}

variable "s3_cdn_cloudfront_origin_access_identity_iam_arn" {
  type        = string
  default     = ""
  description = "Existing cloudfront origin access identity iam arn that is supplied in the s3 bucket policy"
}

variable "s3_cdn_cloudfront_origin_access_control_id" {
  type        = string
  default     = ""
  description = "CloudFront provides two ways to send authenticated requests to an Amazon S3 origin: origin access control (OAC) and origin access identity (OAI). OAC helps you secure your origins, such as for Amazon S3"
}

variable "s3_cdn_origin_shield_enabled" {
  type        = bool
  default     = false
  description = "If enabled, origin shield will be enabled for the default origin"
}

variable "s3_cdn_origin_ssl_protocols" {
  type        = list(string)
  default     = ["TLSv1", "TLSv1.1", "TLSv1.2"]
  description = "The SSL/TLS protocols that you want CloudFront to use when communicating with your origin over HTTPS"
}

variable "s3_cdn_realtime_log_config_arn" {
  type        = string
  default     = null
  description = "The ARN of the real-time log configuration that is attached to this cache behavior"
}

variable "s3_cdn_function_association" {
  type = list(object({
    event_type   = string
    function_arn = string
  }))
  default     = []
  description = "A config block that triggers a CloudFront function with specific actions"
}
