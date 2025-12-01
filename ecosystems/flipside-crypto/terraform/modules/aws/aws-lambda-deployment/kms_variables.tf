# KMS Key Variables
variable "create_kms_key" {
  type        = bool
  default     = false
  description = "Whether to create a KMS key for encryption"
}

variable "create_kms_key_policy" {
  type        = bool
  default     = false
  description = "Whether to create a KMS key policy. This can be true even if create_kms_key is false, allowing management of policies for existing keys."
}

variable "kms_key_name" {
  type        = string
  default     = null
  description = "Name of the KMS key to create"
}

variable "kms_key_description" {
  type        = string
  default     = null
  description = "Description of the KMS key to create"
}

variable "kms_key_deletion_window_in_days" {
  type        = number
  default     = 30
  description = "Number of days before deletion of the KMS key"
}

variable "kms_key_enable_key_rotation" {
  type        = bool
  default     = true
  description = "Whether to enable automatic key rotation"
}

variable "kms_key_aliases" {
  type        = list(string)
  default     = []
  description = "Additional aliases for the KMS key"
}

variable "kms_key_tags" {
  type        = map(string)
  default     = {}
  description = "Tags for the KMS key"
}

# KMS Key Policy Variables
variable "lambda_include_kms_policy" {
  type        = bool
  default     = true
  description = "Whether to include Lambda in the KMS key policy"
  validation {
    condition     = !var.lambda_include_kms_policy || var.create_kms_key_policy
    error_message = "Cannot include Lambda in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_include_lambda_policy" {
  type        = bool
  default     = true
  description = "Whether to include a policy for Lambda in the KMS key"
  validation {
    condition     = !var.kms_key_include_lambda_policy || var.create_kms_key_policy
    error_message = "Cannot include Lambda policy in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_include_api_gateway_policy" {
  type        = bool
  default     = true
  description = "Whether to include a policy for API Gateway in the KMS key"
  validation {
    condition     = !var.kms_key_include_api_gateway_policy || var.create_kms_key_policy
    error_message = "Cannot include API Gateway policy in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_include_s3_policy" {
  type        = bool
  default     = true
  description = "Whether to include a policy for S3 in the KMS key"
  validation {
    condition     = !var.kms_key_include_s3_policy || var.create_kms_key_policy
    error_message = "Cannot include S3 policy in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_include_cloudfront_policy" {
  type        = bool
  default     = true
  description = "Whether to include a policy for CloudFront in the KMS key"
  validation {
    condition     = !var.kms_key_include_cloudfront_policy || var.create_kms_key_policy
    error_message = "Cannot include CloudFront policy in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_include_lambda_edge_policy" {
  type        = bool
  default     = true
  description = "Whether to include a policy for Lambda@Edge in the KMS key"
  validation {
    condition     = !var.kms_key_include_lambda_edge_policy || var.create_kms_key_policy
    error_message = "Cannot include Lambda@Edge policy in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_include_cloudwatch_logs_policy" {
  type        = bool
  default     = true
  description = "Whether to include a policy for CloudWatch Logs in the KMS key"
  validation {
    condition     = !var.kms_key_include_cloudwatch_logs_policy || var.create_kms_key_policy
    error_message = "Cannot include CloudWatch Logs policy in KMS key policy when create_kms_key_policy is false."
  }
}

variable "kms_key_account_ids" {
  type        = list(string)
  default     = []
  description = "Account IDs to allow KMS key access to"
}

variable "kms_key_authorize_all_in_account" {
  type        = bool
  default     = true
  description = "Whether to authorize everybody in the account or just grantees"
}
