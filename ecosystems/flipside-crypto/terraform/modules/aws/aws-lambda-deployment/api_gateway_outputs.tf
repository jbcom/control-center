# API Gateway Outputs

output "api_gateway_id" {
  description = "The API identifier"
  value       = try(module.api_gateway[0].api_id, null)
}

output "api_gateway_arn" {
  description = "The ARN of the API"
  value       = try(module.api_gateway[0].api_arn, null)
}

output "api_gateway_endpoint" {
  description = "URI of the API, of the form https://{api-id}.execute-api.{region}.amazonaws.com for HTTP APIs and wss://{api-id}.execute-api.{region}.amazonaws.com for WebSocket APIs"
  value       = try(module.api_gateway[0].api_endpoint, null)
}

output "api_gateway_execution_arn" {
  description = "The ARN prefix to be used in an aws_lambda_permission's source_arn attribute or in an aws_iam_policy to authorize access to the @connections API"
  value       = try(module.api_gateway[0].api_execution_arn, null)
}

output "api_gateway_stage_arn" {
  description = "The stage ARN"
  value       = try(module.api_gateway[0].stage_arn, null)
}

output "api_gateway_stage_id" {
  description = "The stage identifier"
  value       = try(module.api_gateway[0].stage_id, null)
}

output "api_gateway_stage_invoke_url" {
  description = "The URL to invoke the API pointing to the stage"
  value       = try(module.api_gateway[0].stage_invoke_url, null)
}

output "api_gateway_stage_execution_arn" {
  description = "The ARN prefix to be used in an aws_lambda_permission's source_arn attribute or in an aws_iam_policy to authorize access to the @connections API"
  value       = try(module.api_gateway[0].stage_execution_arn, null)
}

output "api_gateway_domain_name_arn" {
  description = "The ARN of the domain name"
  value       = try(module.api_gateway[0].domain_name_arn, null)
}

output "api_gateway_domain_name_id" {
  description = "The domain name identifier"
  value       = try(module.api_gateway[0].domain_name_id, null)
}

output "api_gateway_domain_name_configuration" {
  description = "The domain name configuration"
  value       = try(module.api_gateway[0].domain_name_configuration, null)
}

output "api_gateway_domain_name_hosted_zone_id" {
  description = "The Amazon Route 53 Hosted Zone ID of the endpoint"
  value       = try(module.api_gateway[0].domain_name_hosted_zone_id, null)
}

output "api_gateway_domain_name_target_domain_name" {
  description = "The target domain name"
  value       = try(module.api_gateway[0].domain_name_target_domain_name, null)
}

output "api_gateway_routes" {
  description = "Map of the routes created and their attributes"
  value       = try(module.api_gateway[0].routes, null)
}

output "api_gateway_integrations" {
  description = "Map of the integrations created and their attributes"
  value       = try(module.api_gateway[0].integrations, null)
}

output "api_gateway_authorizers" {
  description = "Map of API Gateway Authorizer(s) created and their attributes"
  value       = try(module.api_gateway[0].authorizers, null)
}

output "api_gateway_access_logs_cloudwatch_log_group_name" {
  description = "Name of cloudwatch log group created for API Gateway access logs"
  value       = try(aws_cloudwatch_log_group.api_gateway_logs[0].name, null)
}

output "api_gateway_access_logs_cloudwatch_log_group_arn" {
  description = "ARN of cloudwatch log group created for API Gateway access logs"
  value       = try(aws_cloudwatch_log_group.api_gateway_logs[0].arn, null)
}

output "api_gateway_execution_role_name" {
  description = "Name of IAM role used by API Gateway"
  value       = try(aws_iam_role.api_gateway_execution_role[0].name, null)
}

output "api_gateway_execution_role_arn" {
  description = "ARN of IAM role used by API Gateway"
  value       = try(aws_iam_role.api_gateway_execution_role[0].arn, null)
}
