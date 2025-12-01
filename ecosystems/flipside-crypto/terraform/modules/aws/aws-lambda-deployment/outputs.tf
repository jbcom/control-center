# Lambda Function Outputs
output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = module.lambda_function.lambda_function_arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = module.lambda_function.lambda_function_name
}

output "lambda_function_version" {
  description = "The version of the Lambda function"
  value       = module.lambda_function.lambda_function_version
}

output "lambda_function_qualified_arn" {
  description = "The qualified ARN of the Lambda function"
  value       = module.lambda_function.lambda_function_qualified_arn
}

output "lambda_function_invoke_arn" {
  description = "The invoke ARN of the Lambda function"
  value       = module.lambda_function.lambda_function_invoke_arn
}

output "lambda_function_url" {
  description = "The URL of the Lambda function (if enabled)"
  value       = module.lambda_function.lambda_function_url
}

output "lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda function"
  value       = module.lambda_function.lambda_role_arn
}

output "lambda_role_name" {
  description = "The name of the IAM role created for the Lambda function"
  value       = module.lambda_function.lambda_role_name
}

# Lambda Alias Outputs
output "lambda_alias_arn" {
  description = "The ARN of the Lambda alias"
  value       = var.create_alias ? module.lambda_alias.lambda_alias_arn : null
}

output "lambda_alias_name" {
  description = "The name of the Lambda alias"
  value       = var.create_alias ? module.lambda_alias.lambda_alias_name : null
}

output "lambda_alias_invoke_arn" {
  description = "The invoke ARN of the Lambda alias"
  value       = var.create_alias ? module.lambda_alias.lambda_alias_invoke_arn : null
}

# Lambda Deployment Outputs
output "lambda_deployment_app_name" {
  description = "The name of the CodeDeploy application"
  value       = local.create_deployment ? module.lambda_deploy[0].app_name : null
}

output "lambda_deployment_group_name" {
  description = "The name of the CodeDeploy deployment group"
  value       = local.create_deployment ? module.lambda_deploy[0].deployment_group_name : null
}

# ECR Repository Outputs
output "ecr_repository_arn" {
  description = "The ARN of the ECR repository"
  value       = local.create_ecr_repo ? aws_ecr_repository.this[0].arn : null
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = local.create_ecr_repo ? aws_ecr_repository.this[0].repository_url : null
}

output "ecr_repository_name" {
  description = "The name of the ECR repository"
  value       = local.create_ecr_repo ? aws_ecr_repository.this[0].name : null
}

# Docker Image Outputs
output "docker_image_uri" {
  description = "The URI of the Docker image"
  value       = local.create_docker_build ? module.docker_image[0].image_uri : null
}

# API Gateway Outputs
output "api_gateway_api_id" {
  description = "The ID of the API Gateway API"
  value       = local.create_api_gateway ? module.api_gateway[0].api_id : null
}

output "api_gateway_api_endpoint" {
  description = "The endpoint URL of the API Gateway API"
  value       = local.create_api_gateway ? module.api_gateway[0].api_endpoint : null
}

output "api_gateway_api_execution_arn" {
  description = "The execution ARN of the API Gateway API"
  value       = local.create_api_gateway ? module.api_gateway[0].api_execution_arn : null
}

output "api_gateway_domain_name" {
  description = "The custom domain name of the API Gateway API"
  value       = local.create_api_gateway && var.api_gateway_create_domain_name ? module.api_gateway[0].domain_name : null
}

# api_gateway_domain_name_configuration is defined in api_gateway_outputs.tf

output "api_gateway_route_ids" {
  description = "The IDs of the API Gateway routes"
  value       = local.create_api_gateway ? module.api_gateway[0].route_ids : null
}

output "api_gateway_stage" {
  description = "The API Gateway stage"
  value       = local.create_api_gateway && var.api_gateway_create_stage ? module.api_gateway[0].default_stage_id : null
}

output "api_gateway_dns_record" {
  description = "The DNS record created for the API Gateway domain name"
  value       = local.create_api_gateway_dns && local.api_gateway_zone_id != null ? aws_route53_record.api_gateway[0].fqdn : null
}

# S3 CDN Outputs
output "s3_cdn_cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_id : null
}

output "s3_cdn_cloudfront_distribution_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_arn : null
}

output "s3_cdn_cloudfront_distribution_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_domain_name : null
}

output "s3_cdn_cloudfront_distribution_hosted_zone_id" {
  description = "The hosted zone ID of the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_hosted_zone_id : null
}

output "s3_cdn_bucket_name" {
  description = "The name of the S3 bucket"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket : null
}

output "s3_cdn_bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket_arn : null
}

output "s3_cdn_bucket_domain_name" {
  description = "The domain name of the S3 bucket"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket_domain_name : null
}

output "s3_cdn_dns_records" {
  description = "The DNS records created for the S3 CDN"
  value = local.create_s3_cdn_dns && local.s3_cdn_zone_id != null && var.s3_cdn_external_aliases != null ? {
    for alias in var.s3_cdn_external_aliases : alias => aws_route53_record.s3_cdn[alias].fqdn
  } : null
}

output "s3_cdn_dns_records_ipv6" {
  description = "The IPv6 DNS records created for the S3 CDN"
  value = local.create_s3_cdn_dns && local.s3_cdn_zone_id != null && var.s3_cdn_external_aliases != null && var.s3_cdn_ipv6_enabled ? {
    for alias in var.s3_cdn_external_aliases : alias => aws_route53_record.s3_cdn_ipv6[alias].fqdn
  } : null
}

# CloudWatch Alarm Outputs
output "cloudwatch_alarm_arn" {
  description = "The ARN of the CloudWatch alarm"
  value       = module.this.enabled && var.create_cloudwatch_alarm ? aws_cloudwatch_metric_alarm.lambda_errors[0].arn : null
}

output "cloudwatch_alarm_name" {
  description = "The name of the CloudWatch alarm"
  value       = module.this.enabled && var.create_cloudwatch_alarm ? aws_cloudwatch_metric_alarm.lambda_errors[0].alarm_name : null
}

# SSM Parameter Outputs
output "ssm_parameter_names" {
  description = "The names of the SSM parameters"
  value = module.this.enabled && var.create_ssm_parameters ? {
    for k, v in var.ssm_parameters : k => aws_ssm_parameter.this[k].name
  } : null
}

output "ssm_parameter_arns" {
  description = "The ARNs of the SSM parameters"
  value = module.this.enabled && var.create_ssm_parameters ? {
    for k, v in var.ssm_parameters : k => aws_ssm_parameter.this[k].arn
  } : null
}

# KMS Key Outputs
output "kms_key_arn" {
  description = "The ARN of the KMS key"
  value       = local.create_kms_key ? module.kms_key[0].arn : null
}

output "kms_key_id" {
  description = "The ID of the KMS key"
  value       = local.create_kms_key ? module.kms_key[0].key_id : null
}

output "kms_key_alias" {
  description = "The alias of the KMS key"
  value       = local.create_kms_key ? module.kms_key[0].default_alias : null
}

output "effective_kms_key_arn" {
  description = "The ARN of the KMS key that is actually used (either the created one or the provided one)"
  value       = local.effective_kms_key_arn
}
