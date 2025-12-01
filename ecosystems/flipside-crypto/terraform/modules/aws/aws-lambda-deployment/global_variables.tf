# Global Variables for Lambda Deployment Module
# These variables can be used to override specific settings across different components

# DNS Configuration
variable "zone_id" {
  type        = string
  default     = null
  description = "ID of the Route53 hosted zone to use for DNS records. If provided, overrides component-specific zone IDs."
}

variable "hosted_zone_name" {
  type        = string
  default     = null
  description = "Name of the Route53 hosted zone to use for DNS records. If provided and zone_id is not set, this will be used to look up the zone."
}

variable "private_zone" {
  type        = bool
  default     = false
  description = "Whether the hosted zone is private or public."
}


# Certificate Configuration
variable "certificate_arn" {
  type        = string
  default     = null
  description = "ARN of the ACM certificate to use for HTTPS. If provided, overrides component-specific certificate ARNs."
}

# KMS Configuration
variable "kms_key_arn" {
  type        = string
  default     = null
  description = "ARN of the KMS key to use for encryption. If provided, overrides component-specific KMS key ARNs."
}

# Logging Configuration
variable "log_retention_days" {
  type        = number
  default     = null
  description = "Number of days to retain logs in CloudWatch. If provided, overrides component-specific log retention settings."
}

variable "enable_access_logging" {
  type        = bool
  default     = null
  description = "Whether to enable access logging for resources that support it. If provided, overrides component-specific access logging settings."
}

variable "access_log_bucket_name" {
  type        = string
  default     = null
  description = "Name of the S3 bucket to store access logs. If provided, overrides component-specific access log bucket settings."
}

# Deployment Configuration
variable "wait_for_deployment" {
  type        = bool
  default     = null
  description = "Whether to wait for resource deployments to complete. If provided, overrides component-specific deployment wait settings."
}

# Cache Configuration
variable "default_ttl" {
  type        = number
  default     = null
  description = "Default TTL for cached content in seconds. If provided, overrides component-specific TTL settings."
}

variable "min_ttl" {
  type        = number
  default     = null
  description = "Minimum TTL for cached content in seconds. If provided, overrides component-specific TTL settings."
}

variable "max_ttl" {
  type        = number
  default     = null
  description = "Maximum TTL for cached content in seconds. If provided, overrides component-specific TTL settings."
}
