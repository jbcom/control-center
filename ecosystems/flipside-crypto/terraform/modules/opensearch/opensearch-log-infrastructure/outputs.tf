# S3 Bucket outputs
output "logs_bucket_id" {
  value       = module.logs_bucket.bucket_id
  description = "The name of the S3 bucket where logs are stored"
}

output "logs_bucket_arn" {
  value       = module.logs_bucket.bucket_arn
  description = "The ARN of the S3 bucket where logs are stored"
}

# SQS Queue outputs
output "logs_queue_url" {
  value       = aws_sqs_queue.logs_queue.url
  description = "The URL of the SQS queue for log processing"
}

output "logs_queue_arn" {
  value       = aws_sqs_queue.logs_queue.arn
  description = "The ARN of the SQS queue for log processing"
}

# Lambda outputs
output "transformer_function_name" {
  value       = module.firehose_transformer.function_name
  description = "The name of the Lambda function used for log transformation"
}

output "transformer_function_arn" {
  value       = module.firehose_transformer.arn
  description = "The ARN of the Lambda function used for log transformation"
}

output "transformer_role_arn" {
  value       = module.firehose_transformer.role_arn
  description = "The ARN of the IAM role used by the transformer Lambda function"
}

# Cross-account role output
output "cross_account_role_arn" {
  value       = module.opensearch_cross_account_role.arn
  description = "The ARN of the cross-account role for member account access"
} 