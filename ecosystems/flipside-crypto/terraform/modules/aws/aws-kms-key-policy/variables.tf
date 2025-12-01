variable "kms_key_id" {
  description = "The ID of the KMS key to attach the policy to"
  type        = string
}

variable "kms_policy_enabled" {
  description = "If set to true will create the KMS key policy in AWS, otherwise will only output policy as JSON"
  type        = bool
  default     = false
}

variable "source_policy_documents" {
  description = "List of IAM policy documents that are merged together into the exported document. Statements must have unique sids."
  type        = list(string)
  default     = []
}

variable "override_policy_documents" {
  description = "List of IAM policy documents that are merged together into the exported document. In merging, statements with non-blank sids will override statements with the same sid."
  type        = list(string)
  default     = []
}

variable "account_ids" {
  description = "List of AWS account IDs to grant access to the key"
  type        = list(string)
  default     = []
}

variable "grantees" {
  description = "List of AWS principals to grant access to the key"
  type        = list(string)
  default     = []
}

variable "authorize_all_in_account" {
  description = "Whether to authorize all principals in the account to use the key"
  type        = bool
  default     = false
}

variable "iam_statement_actions" {
  description = "List of IAM actions to allow for the key"
  type        = list(string)
  default     = ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"]
}

variable "grant_operations" {
  description = "List of KMS operations to grant to the grantees"
  type        = list(string)
  default     = ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"]
}

# Lambda policy variables
variable "include_lambda_policy" {
  description = "Whether to include Lambda policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "lambda_function_arns" {
  description = "List of Lambda function ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

# API Gateway policy variables
variable "include_api_gateway_policy" {
  description = "Whether to include API Gateway policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "api_gateway_arns" {
  description = "List of API Gateway ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

variable "api_gateway_api_ids" {
  description = "API Gateway API IDs to allow access to the key"
  type        = list(string)
  default     = []
}

# S3 policy variables
variable "include_s3_policy" {
  description = "Whether to include S3 policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

# CloudFront policy variables
variable "include_cloudfront_policy" {
  description = "Whether to include CloudFront policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "cloudfront_distribution_arns" {
  description = "List of CloudFront distribution ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

variable "include_lambda_edge_policy" {
  description = "Whether to include a policy for Lambda@Edge"
  type        = bool
  default     = false
}

variable "cloudfront_distribution_ids" {
  description = "CloudFront distribution IDs to allow access to the key"
  type        = list(string)
  default     = []
}

# CloudWatch Logs policy variables
variable "include_cloudwatch_logs_policy" {
  description = "Whether to include CloudWatch Logs policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "cloudwatch_log_group_arns" {
  description = "List of CloudWatch Log Group ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

# CloudTrail policy variables
variable "include_cloudtrail_policy" {
  description = "Whether to include CloudTrail policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "cloudtrail_arns" {
  description = "List of CloudTrail ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

# DynamoDB policy variables
variable "include_dynamodb_policy" {
  description = "Whether to include DynamoDB policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

variable "dynamodb_principals" {
  description = "List of principals to allow to use DynamoDB with this key"
  type        = list(string)
  default     = []
}

variable "enable_dynamodb_for_all_grantees" {
  description = "Whether to enable dynamodb for all grantees"
  type        = bool
  default     = false
}

# Autoscaling policy variables
variable "include_autoscaling_policy" {
  description = "Whether to include Autoscaling policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "autoscaling_group_arns" {
  description = "List of Autoscaling group ARNs to grant access to the key"
  type        = list(string)
  default     = []
}

variable "enable_autoscaling_for_all_account_ids" {
  description = "Whether to enable autoscaling for all account IDs or just the caller account"
  type        = bool
  default     = false
}

# Organization policy variables
variable "include_organization_policy" {
  description = "Whether to include Organization policy in the KMS key policy"
  type        = bool
  default     = false
}

variable "organization_id" {
  description = "The ID of the AWS Organization to grant access to the key"
  type        = string
  default     = ""
}
