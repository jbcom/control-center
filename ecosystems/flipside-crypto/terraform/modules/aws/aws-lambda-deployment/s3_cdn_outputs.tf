# S3 CDN Outputs

output "s3_cdn_cf_id" {
  description = "ID of AWS CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_id : null
}

output "s3_cdn_cf_arn" {
  description = "ARN of AWS CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_arn : null
}

output "s3_cdn_cf_status" {
  description = "Current status of the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_status : null
}

output "s3_cdn_cf_domain_name" {
  description = "Domain name corresponding to the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_domain_name : null
}

output "s3_cdn_cf_etag" {
  description = "Current version of the CloudFront distribution's information"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_etag : null
}

output "s3_cdn_cf_hosted_zone_id" {
  description = "CloudFront Route 53 zone ID"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_hosted_zone_id : null
}

output "s3_cdn_cf_origin_access_identity_iam_arn" {
  description = "CloudFront Origin Access Identity IAM ARN"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_identity_iam_arn : null
}

output "s3_cdn_cf_origin_access_control_id" {
  description = "CloudFront Origin Access Control ID"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_access_control_id : null
}

output "s3_cdn_cf_s3_canonical_user_id" {
  description = "Canonical user ID for CloudFront Origin Access Identity"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_s3_canonical_user_id : null
}

output "s3_cdn_cf_origin_ids" {
  description = "List of Origin IDs in the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_origin_ids : null
}

output "s3_cdn_cf_primary_origin_id" {
  description = "The ID of the origin created by this module"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_primary_origin_id : null
}

output "s3_cdn_cf_origin_groups" {
  description = "List of Origin Groups in the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].cf_origin_groups : null
}

output "s3_cdn_cf_aliases" {
  description = "Aliases of the CloudFront distribution"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].aliases : null
}

output "s3_cdn_s3_bucket" {
  description = "Name of origin S3 bucket"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket : null
}

output "s3_cdn_s3_bucket_arn" {
  description = "ARN of origin S3 bucket"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket_arn : null
}

output "s3_cdn_s3_bucket_domain_name" {
  description = "Domain of origin S3 bucket"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket_domain_name : null
}

output "s3_cdn_s3_bucket_policy" {
  description = "Final computed S3 bucket policy"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].s3_bucket_policy : null
}

output "s3_cdn_logs" {
  description = "Log bucket resource"
  value       = local.create_s3_cdn ? module.cloudfront_s3_cdn[0].logs : null
}

output "s3_cdn_lambda_function_association" {
  description = "Lambda@Edge function association configuration"
  value       = local.create_s3_cdn ? concat(local.lambda_edge_function_association, var.s3_cdn_additional_lambda_function_association) : null
}

output "s3_cdn_lambda_function_arn" {
  description = "ARN of the Lambda function used for Lambda@Edge"
  value       = local.create_s3_cdn ? local.lambda_function_arn : null
}

output "s3_cdn_lambda_function_qualifier" {
  description = "Qualifier (alias or version) of the Lambda function used for Lambda@Edge"
  value       = local.create_s3_cdn ? local.lambda_function_qualifier : null
}
