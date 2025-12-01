/**
 * Label Modules
 */

module "logs_bucket_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  attributes = ["storage"]
  context    = var.context
}

module "logs_queue_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  attributes = ["queue"]
  context    = var.context

  # Limit ID length for queue resources
  id_length_limit = 64
}

module "cross_account_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  attributes = ["cross-account"]
  context    = var.context
}

/**
 * Data Sources and Locals
 */

# Policy for S3 to send messages to SQS queue
data "aws_iam_policy_document" "logs_queue_policy" {
  statement {
    sid       = "AllowS3ToSendMessages"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.logs_queue.arn]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [module.logs_bucket.bucket_arn]
    }
  }
}

# Lambda transformer policy
data "aws_iam_policy_document" "lambda_transformer_policy" {
  statement {
    effect = "Allow"
    actions = [
      "firehose:PutRecordBatch"
    ]
    # Use wildcard since Firehose doesn't exist yet
    resources = ["arn:aws:firehose:${local.region}:${local.account_id}:deliverystream/*"]
  }
}

# Cross-account access policy
data "aws_iam_policy_document" "cross_account_access" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]
    resources = [
      module.logs_bucket.bucket_arn,
      "${module.logs_bucket.bucket_arn}/*"
    ]
  }
}

locals {
  lambda_transformer_base_zip_path = coalesce(var.lambda_transformer_zip_path, path.cwd)
  lambda_transformer_zip_path      = endswith(local.lambda_transformer_base_zip_path, ".zip") ? local.lambda_transformer_base_zip_path : "${local.lambda_transformer_base_zip_path}/lambda_transformer.zip"
}

/**
 * Cross-Account Role
 */

module "opensearch_cross_account_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  # Label module attributes
  context    = var.context
  attributes = ["cross-account"]

  role_description      = "Allow member accounts to access log storage resources"
  policy_document_count = 1
  policy_documents      = [data.aws_iam_policy_document.cross_account_access.json]

  # Allow member accounts to assume this role
  assume_role_actions = ["sts:AssumeRole"]
  principals = {
    AWS = ["arn:aws:iam::${local.account_id}:root"]
  }
}

/**
 * S3 Bucket Resources
 */

module "logs_bucket" {
  source  = "cloudposse/s3-bucket/aws"
  version = "4.10.0"

  # Label settings
  context    = var.context
  tenant     = "fsc"
  attributes = ["storage"]

  # Bucket configuration
  acl                          = null # Disabled in favor of bucket policy
  enabled                      = true
  allow_encrypted_uploads_only = true
  allow_ssl_requests_only      = true
  force_destroy                = true # Allow Terraform to destroy the bucket
  ignore_public_acls           = true
  restrict_public_buckets      = true
  kms_master_key_arn           = var.kms_key_arn
  block_public_acls            = true
  block_public_policy          = true
  versioning_enabled           = true
  s3_object_ownership          = "BucketOwnerEnforced"
  lifecycle_configuration_rules = [
    {
      id      = "cleanup-old-logs"
      enabled = true
      expiration = {
        days = 30
      }
    }
  ]

  # Server-side encryption
  sse_algorithm      = "aws:kms"
  bucket_key_enabled = true

  # Event notifications
  event_notification_details = {
    enabled = true
    queue_list = [
      {
        queue_arn     = aws_sqs_queue.logs_queue.arn
        events        = ["s3:ObjectCreated:*"]
        filter_prefix = "logs/"
      }
    ]
  }

  # Necessary permissions for cross-account access if applicable
  privileged_principal_arns = [
    {
      "${module.opensearch_cross_account_role.arn}" = ["firehose/"]
    }
  ]

  privileged_principal_actions = [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket",
    "s3:GetBucketLocation"
  ]
}

/**
 * SQS Resources
 */

resource "aws_sqs_queue" "logs_queue" {
  name = module.logs_queue_label.id

  # Queue settings aligned with AWS sample
  visibility_timeout_seconds = 300
  message_retention_seconds  = 345600 # 4 days

  # Encryption settings - use KMS
  kms_master_key_id = var.kms_key_arn

  # Other settings
  delay_seconds             = 0
  max_message_size          = 262144
  receive_wait_time_seconds = 0

  tags = module.logs_queue_label.tags
}

resource "aws_sqs_queue_policy" "logs_queue_policy" {
  queue_url = aws_sqs_queue.logs_queue.url
  policy    = data.aws_iam_policy_document.logs_queue_policy.json
}

/**
 * Lambda Resources
 */

data "archive_file" "lambda_transformer" {
  type        = "zip"
  source_file = "${path.module}/files/kdf-opensearch-transform-v2.py"
  output_path = local.lambda_transformer_zip_path
}

module "firehose_transformer" {
  source  = "cloudposse/lambda-function/aws"
  version = "0.6.1"

  # Label module attributes
  context = var.context
  name    = "transformer"

  # Basic settings
  function_name = "grafana-transformer"
  description   = "Transform CloudWatch logs for OpenSearch ingestion"
  handler       = "kdf-opensearch-transform-v2.lambda_handler"
  runtime       = "python3.13"
  timeout       = var.lambda_transformer_timeout
  memory_size   = var.lambda_transformer_memory

  # Deployment package
  filename         = data.archive_file.lambda_transformer.output_path
  source_code_hash = filebase64sha256(data.archive_file.lambda_transformer.output_path)

  # Enhanced monitoring and observability
  cloudwatch_lambda_insights_enabled = var.lambda_insights_enabled

  # Security and encryption
  cloudwatch_logs_kms_key_arn = coalesce(var.lambda_logs_kms_key_arn, var.kms_key_arn)
  kms_key_arn                 = coalesce(var.lambda_kms_key_arn, var.kms_key_arn)

  # Log retention
  cloudwatch_logs_retention_in_days = var.lambda_logs_retention_days

  inline_iam_policy = data.aws_iam_policy_document.lambda_transformer_policy.json
}
