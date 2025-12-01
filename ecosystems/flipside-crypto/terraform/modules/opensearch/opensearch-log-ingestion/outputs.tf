# Firehose outputs
output "firehose_stream_name" {
  value       = aws_kinesis_firehose_delivery_stream.opensearch_stream.name
  description = "The name of the Kinesis Firehose delivery stream"
}

output "firehose_stream_arn" {
  value       = aws_kinesis_firehose_delivery_stream.opensearch_stream.arn
  description = "The ARN of the Kinesis Firehose delivery stream"
}

output "firehose_role_arn" {
  value       = module.firehose_role.arn
  description = "The ARN of the IAM role used by Firehose"
}

# CloudWatch outputs
output "firehose_log_group_name" {
  value       = aws_cloudwatch_log_group.firehose_logs.name
  description = "The name of the CloudWatch log group for Firehose logs"
}

output "firehose_log_group_arn" {
  value       = aws_cloudwatch_log_group.firehose_logs.arn
  description = "The ARN of the CloudWatch log group for Firehose logs"
}

# Pipeline outputs
output "ingestion_pipeline_name" {
  value       = aws_osis_pipeline.logs_pipeline.pipeline_name
  description = "The name of the OpenSearch ingestion pipeline"
}

# CloudFormation StackSet outputs
output "stackset_name" {
  value       = aws_cloudformation_stack_set.log_subscription.name
  description = "The name of the CloudFormation StackSet for log subscription"
}

output "stackset_id" {
  value       = aws_cloudformation_stack_set.log_subscription.id
  description = "The ID of the CloudFormation StackSet for log subscription"
} 