locals {
  # Determine which KMS key to use
  kms_key_id = local.create_kms_key ? module.kms_key[0].id : (var.global_kms_key_arn != null ? var.global_kms_key_arn : var.kms_key_arn)

  # Resources that will use the KMS key
  lambda_function_names       = local.lambda.enabled ? [module.lambda_function.lambda_function_name] : []
  api_gateway_api_ids         = local.api_gateway.enabled ? [module.api_gateway[0].api_id] : []
  s3_bucket_names             = local.s3_cdn.enabled ? [module.cloudfront_s3_cdn[0].s3_bucket] : []
  cloudfront_distribution_ids = local.s3_cdn.enabled ? [module.cloudfront_s3_cdn[0].cf_id] : []
}

module "kms_key" {
  count  = local.create_kms_key ? 1 : 0
  source = "../aws-kms-key"

  kms_key_name            = local.kms.key_name != null ? local.kms.key_name : "${module.this.id}-key"
  kms_key_description     = local.kms.key_description != null ? local.kms.key_description : "${module.this.id} KMS key for Lambda deployment"
  deletion_window_in_days = local.kms.key_deletion_window_in_days
  enable_key_rotation     = local.kms.key_enable_key_rotation
  kms_key_aliases         = local.kms.key_aliases
  tags                    = merge(module.this.tags, local.kms.key_tags)

  # Account access
  account_ids              = local.kms.key_account_ids
  authorize_all_in_account = local.kms.key_authorize_all_in_account

  # We'll manage the KMS key policy separately if requested
  manage_kms_key_policy = false
}

# Separate KMS key policy module to allow managing policies for existing keys
module "kms_key_policy" {
  count  = local.kms.create_key_policy ? 1 : 0
  source = "../aws-kms-key-policy"

  kms_key_id         = local.kms_key_id
  kms_policy_enabled = true

  # Account access
  account_ids              = local.kms.key_account_ids
  authorize_all_in_account = local.kms.key_authorize_all_in_account

  # Service-specific policies
  include_lambda_policy = local.kms.lambda_include_kms_policy
  lambda_function_arns  = local.lambda_function_names

  include_api_gateway_policy = local.kms.key_include_api_gateway_policy && local.api_gateway.enabled
  api_gateway_arns           = local.api_gateway_api_ids

  include_s3_policy = local.kms.key_include_s3_policy && local.s3_cdn.enabled
  s3_bucket_arns    = local.s3_bucket_names

  include_cloudfront_policy    = local.kms.key_include_cloudfront_policy && local.s3_cdn.enabled
  cloudfront_distribution_arns = local.cloudfront_distribution_ids

  include_cloudwatch_logs_policy = local.kms.key_include_cloudwatch_logs_policy
}
