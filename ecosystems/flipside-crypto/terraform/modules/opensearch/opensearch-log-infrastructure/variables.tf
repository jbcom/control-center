variable "lambda_transformer_zip_path" {
  description = "The path to the lambda transformer zip file. Defaults to storing in the current working directory."
  type        = string
  default     = null
}

variable "lambda_transformer_timeout" {
  description = "The amount of time the Lambda function has to run in seconds. Higher values are needed for processing larger log batches."
  type        = number
  default     = 300 # 5 minutes, which is more appropriate for log processing
}

variable "lambda_transformer_memory" {
  description = "The amount of memory available to the Lambda function in MB. Higher values also give more CPU allocation."
  type        = number
  default     = 512 # 512MB provides better CPU allocation and memory headroom
}

variable "lambda_insights_enabled" {
  description = "Whether to enable CloudWatch Lambda Insights for enhanced monitoring"
  type        = bool
  default     = true
}

variable "lambda_logs_kms_key_arn" {
  description = "ARN of the KMS key to use for encrypting Lambda CloudWatch logs"
  type        = string
  default     = null
}

variable "lambda_logs_retention_days" {
  description = "Number of days to retain Lambda CloudWatch logs"
  type        = number
  default     = 30
}

variable "lambda_kms_key_arn" {
  description = "ARN of the KMS key to use for Lambda environment variable encryption"
  type        = string
  default     = null
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