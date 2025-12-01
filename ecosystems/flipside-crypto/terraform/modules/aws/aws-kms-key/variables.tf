variable "kms_key_name" {
  type        = string
  description = "KMS key name"
}

variable "kms_key_description" {
  type        = string
  default     = null
  description = "Description of the KMS key"
}

variable "deletion_window_in_days" {
  type        = number
  default     = 30
  description = "Number of days before deletion of the KMS key"
}

variable "enable_key_rotation" {
  type        = bool
  default     = true
  description = "Whether to enable automatic key rotation"
}

variable "key_usage" {
  type        = string
  default     = "ENCRYPT_DECRYPT"
  description = "The usage of the KMS key"
}

variable "customer_master_key_spec" {
  type        = string
  default     = "SYMMETRIC_DEFAULT"
  description = "Specifies the type of KMS key to create"
}

variable "create_aliases" {
  type        = bool
  default     = true
  description = "Whether to create aliases or not"
}

variable "kms_key_aliases" {
  type        = list(string)
  default     = []
  description = "Additional aliases for the KMS key"
}

variable "account_ids" {
  type        = list(string)
  default     = []
  description = "Account IDs to allow KMS key access to"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags for resources"
}

variable "include_autoscaling_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for autoscaling"
}

variable "enable_autoscaling_for_all_account_ids" {
  type        = bool
  default     = false
  description = "Whether to enable autoscaling for all account IDs or just the caller account"
}

variable "include_dynamodb_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for DynamoDB"
}

variable "enable_dynamodb_for_all_grantees" {
  type        = bool
  default     = false
  description = "Whether to enable dynamodb for all grantees"
}

variable "dynamodb_principals" {
  type        = list(string)
  default     = []
  description = "Principals to allow to use DynamoDB with this key"
}

variable "include_cloudtrail_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for CloudTrail"
}

variable "include_cloudwatch_logs_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for CloudWatch logs"
}

variable "include_lambda_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for Lambda"
}

variable "lambda_function_names" {
  type        = list(string)
  default     = []
  description = "Lambda function names to allow access to the key"
}

variable "include_api_gateway_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for API Gateway"
}

variable "api_gateway_api_ids" {
  type        = list(string)
  default     = []
  description = "API Gateway API IDs to allow access to the key"
}

variable "include_s3_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for S3"
}

variable "s3_bucket_names" {
  type        = list(string)
  default     = []
  description = "S3 bucket names to allow access to the key"
}

variable "include_cloudfront_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for CloudFront"
}

variable "cloudfront_distribution_ids" {
  type        = list(string)
  default     = []
  description = "CloudFront distribution IDs to allow access to the key"
}

variable "include_lambda_edge_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy for Lambda@Edge"
}

variable "source_policy_documents" {
  type        = list(string)
  default     = []
  description = "Source policy documents"
}

variable "override_policy_documents" {
  type        = list(string)
  default     = []
  description = "Override policy documents"
}

variable "grantees" {
  type        = list(string)
  default     = []
  description = "Principals to grant access to the key"
}

variable "grant_operations" {
  type = list(string)
  default = [
    "DescribeKey",
    "Sign",
    "Verify",
    "Decrypt",
    "Encrypt",
    "ReEncryptFrom",
    "ReEncryptTo",
    "GenerateDataKey",
    "GenerateDataKeyWithoutPlaintext",
  ]
  description = "Operations to grant"
}

variable "iam_statement_actions" {
  type = list(string)
  default = [
    "kms:Encrypt",
    "kms:Decrypt",
    "kms:ReEncrypt*",
    "kms:GenerateDataKey*",
    "kms:DescribeKey",
    "kms:CreateGrant",
  ]
  description = "KMS statement actions"
}

variable "organization_id" {
  type        = string
  default     = ""
  description = "Optional organization ID to authorize for the KMS key"
}

variable "include_organization_policy" {
  type        = bool
  default     = false
  description = "Whether to include a policy allowing organization access to the key"
}

variable "authorize_all_in_account" {
  type        = bool
  default     = true
  description = "Whether to authorize everybody in the account or just grantees"
}

variable "manage_kms_key_policy" {
  type        = bool
  default     = true
  description = "Whether to manage the KMS key policy using the aws-kms-key-policy module"
}
