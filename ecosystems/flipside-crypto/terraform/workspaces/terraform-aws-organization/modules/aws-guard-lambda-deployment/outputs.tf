output "lambda_function_arn" {
  description = "The ARN of the Lambda Function"
  value       = module.guard_lambda.lambda_function_arn
}

output "lambda_function_name" {
  description = "The name of the Lambda Function"
  value       = module.guard_lambda.lambda_function_name
}

output "lambda_function_qualified_arn" {
  description = "The ARN identifying your Lambda Function Version"
  value       = module.guard_lambda.lambda_function_qualified_arn
}

output "lambda_function_version" {
  description = "Latest published version of Lambda Function"
  value       = module.guard_lambda.lambda_function_version
}

output "lambda_alias_arn" {
  description = "The ARN of the Lambda alias"
  value       = module.guard_alias.lambda_alias_arn
}

output "lambda_alias_name" {
  description = "The name of the Lambda alias"
  value       = module.guard_alias.lambda_alias_name
}

output "cloudwatch_log_group_name" {
  description = "The name of the Cloudwatch Log Group"
  value       = module.guard_lambda.lambda_cloudwatch_log_group_name
}

output "cloudwatch_log_group_arn" {
  description = "The ARN of the Cloudwatch Log Group"
  value       = module.guard_lambda.lambda_cloudwatch_log_group_arn
}

output "dead_letter_queue_arn" {
  description = "The ARN of the dead letter queue"
  value       = local.enabled_from_cloudposse_context ? aws_sqs_queue.guard_dlq[0].arn : null
}

output "dead_letter_queue_name" {
  description = "The name of the dead letter queue"
  value       = local.enabled_from_cloudposse_context ? aws_sqs_queue.guard_dlq[0].name : null
}

output "eventbridge_rule_arn" {
  description = "The ARN of the EventBridge rule"
  value       = local.enabled_from_cloudposse_context ? aws_cloudwatch_event_rule.guard_schedule[0].arn : null
}

output "eventbridge_rule_name" {
  description = "The name of the EventBridge rule"
  value       = local.enabled_from_cloudposse_context ? aws_cloudwatch_event_rule.guard_schedule[0].name : null
}

output "codedeploy_app_name" {
  description = "The name of the CodeDeploy application"
  value       = module.guard_deploy.codedeploy_app_name
}

output "codedeploy_deployment_group_name" {
  description = "The name of the CodeDeploy deployment group"
  value       = module.guard_deploy.codedeploy_deployment_group_name
}

output "cloudwatch_alarm_arn" {
  description = "The ARN of the CloudWatch alarm for DLQ messages"
  value       = local.enabled_from_cloudposse_context ? aws_cloudwatch_metric_alarm.guard_dlq_alarm[0].arn : null
}

output "deployment_notifications_topic_arn" {
  description = "The ARN of the deployment notifications SNS topic"
  value       = local.enabled_from_cloudposse_context ? aws_sns_topic.deployment_notifications[0].arn : null
}

output "deployment_notifications_topic_name" {
  description = "The name of the deployment notifications SNS topic"
  value       = local.enabled_from_cloudposse_context ? aws_sns_topic.deployment_notifications[0].name : null
}

output "deployment_failures_topic_arn" {
  description = "The ARN of the deployment failures SNS topic"
  value       = local.enabled_from_cloudposse_context ? aws_sns_topic.deployment_failures[0].arn : null
}

output "deployment_failures_topic_name" {
  description = "The name of the deployment failures SNS topic"
  value       = local.enabled_from_cloudposse_context ? aws_sns_topic.deployment_failures[0].name : null
}

# Additional useful outputs from the submodules
output "lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda Function"
  value       = module.guard_lambda.lambda_role_arn
}

output "lambda_role_name" {
  description = "The name of the IAM role created for the Lambda Function"
  value       = module.guard_lambda.lambda_role_name
}

output "lambda_function_invoke_arn" {
  description = "The Invoke ARN of the Lambda Function"
  value       = module.guard_lambda.lambda_function_invoke_arn
}

output "lambda_alias_invoke_arn" {
  description = "The ARN to be used for invoking Lambda Function from API Gateway"
  value       = module.guard_alias.lambda_alias_invoke_arn
}

output "codedeploy_iam_role_name" {
  description = "Name of IAM role used by CodeDeploy"
  value       = module.guard_deploy.codedeploy_iam_role_name
}
