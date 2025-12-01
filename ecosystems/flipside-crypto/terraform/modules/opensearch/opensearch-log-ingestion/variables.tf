variable "opensearch_collection_endpoint" {
  description = "The endpoint URL for the OpenSearch collection where logs will be sent"
  type        = string
}

variable "opensearch_collection_name" {
  description = "The name of the OpenSearch collection where logs will be sent"
  type        = string
}

# Infrastructure module outputs needed
variable "logs_bucket_id" {
  description = "The name of the S3 bucket where logs are stored"
  type        = string
}

variable "logs_bucket_arn" {
  description = "The ARN of the S3 bucket where logs are stored"
  type        = string
}

variable "logs_queue_url" {
  description = "The URL of the SQS queue for log processing"
  type        = string
}

variable "logs_queue_arn" {
  description = "The ARN of the SQS queue for log processing"
  type        = string
}

variable "transformer_function_arn" {
  description = "The ARN of the Lambda function used for log transformation"
  type        = string
}

variable "transformer_role_arn" {
  description = "The ARN of the IAM role used by the transformer Lambda function"
  type        = string
}

variable "cross_account_role_arn" {
  description = "The ARN of the cross-account role for member account access"
  type        = string
}

variable "kms_key_arn" {
  description = "ARN of the KMS key to use for encryption"
  type        = string
  default     = null
}

variable "context" {
  description = "The context for the module"
  type        = any
}

variable "organization_unit_deployment_targets" {
  description = "The organization unit IDs to deploy the stack set to"
  type        = list(string)
  default     = []
}

variable "lambda_transformer_timeout" {
  description = "The amount of time the Lambda function has to run in seconds"
  type        = number
  default     = 300
}

variable "lambda_transformer_memory" {
  description = "The amount of memory available to the Lambda function in MB"
  type        = number
  default     = 256
}

variable "lambda_insights_enabled" {
  description = "Whether to enable Lambda Insights for enhanced monitoring"
  type        = bool
  default     = true
}

variable "lambda_logs_kms_key_arn" {
  description = "KMS key ARN to use for encrypting Lambda CloudWatch logs"
  type        = string
  default     = null
}

variable "lambda_kms_key_arn" {
  description = "KMS key ARN to use for encrypting Lambda function"
  type        = string
  default     = null
}

variable "lambda_logs_retention_days" {
  description = "Number of days to retain Lambda CloudWatch logs"
  type        = number
  default     = 30
} 