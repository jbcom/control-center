resource "aws_kms_key" "default" {
  deletion_window_in_days  = var.deletion_window_in_days
  enable_key_rotation      = var.enable_key_rotation
  description              = coalesce(var.kms_key_description, "${var.kms_key_name} KMS key")
  key_usage                = var.key_usage
  customer_master_key_spec = var.customer_master_key_spec
  tags                     = merge(var.tags, { Name = var.kms_key_name })
}

resource "aws_kms_alias" "default" {
  count         = var.create_aliases ? 1 : 0
  name          = "alias/${trimprefix(var.kms_key_name, "alias/")}"
  target_key_id = aws_kms_key.default.id
}

resource "aws_kms_alias" "additional_aliases" {
  for_each      = var.create_aliases ? toset(var.kms_key_aliases) : []
  name          = "alias/${trimprefix(each.key, "alias/")}"
  target_key_id = aws_kms_key.default.id
}

module "kms_key_policy" {
  source = "../aws-kms-key-policy"

  kms_key_id         = aws_kms_key.default.key_id
  kms_policy_enabled = var.manage_kms_key_policy

  # Pass through variables
  source_policy_documents   = var.source_policy_documents
  override_policy_documents = var.override_policy_documents
  account_ids               = var.account_ids
  grantees                  = var.grantees
  authorize_all_in_account  = var.authorize_all_in_account
  iam_statement_actions     = var.iam_statement_actions
  grant_operations          = var.grant_operations

  # Policy-specific variables
  include_lambda_policy = var.include_lambda_policy
  lambda_function_arns  = var.lambda_function_names

  include_api_gateway_policy = var.include_api_gateway_policy
  api_gateway_arns           = var.api_gateway_api_ids

  include_s3_policy = var.include_s3_policy
  s3_bucket_arns    = var.s3_bucket_names

  include_cloudfront_policy    = var.include_cloudfront_policy
  cloudfront_distribution_arns = var.cloudfront_distribution_ids

  include_cloudwatch_logs_policy = var.include_cloudwatch_logs_policy

  include_cloudtrail_policy = var.include_cloudtrail_policy

  include_dynamodb_policy = var.include_dynamodb_policy
  dynamodb_table_arns     = var.dynamodb_principals

  include_autoscaling_policy = var.include_autoscaling_policy

  include_organization_policy = var.include_organization_policy
  organization_id             = var.organization_id
}
