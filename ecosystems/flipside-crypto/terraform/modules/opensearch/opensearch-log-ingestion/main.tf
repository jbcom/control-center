/**
 * Label Modules
 */

module "firehose_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  attributes = ["firehose"]
  context    = var.context
}

module "logs_pipeline_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  attributes = ["pipeline"]
  context    = var.context
}

module "logs_index_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  attributes = ["index"]
  context    = var.context
}

/**
 * CloudWatch Resources
 */

resource "aws_cloudwatch_log_group" "firehose_logs" {
  name              = "/aws/kinesisfirehose/${module.firehose_label.id}"
  retention_in_days = 30

  tags = module.firehose_label.tags
}

/**
 * IAM Roles and Policies
 */

data "aws_iam_policy_document" "firehose_permissions" {
  # S3 permissions
  statement {
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject"
    ]
    resources = [
      var.logs_bucket_arn,
      "${var.logs_bucket_arn}/*"
    ]
  }

  # Lambda permissions
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
      "lambda:GetFunctionConfiguration"
    ]
    resources = [
      var.transformer_function_arn,
      "${var.transformer_function_arn}:*"
    ]
  }

  # CloudWatch Logs permissions
  statement {
    effect = "Allow"
    actions = [
      "logs:PutLogEvents",
      "logs:CreateLogStream",
      "logs:CreateLogGroup",
      "logs:DescribeLogStreams",
      "logs:DescribeLogGroups"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

module "firehose_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  # Label module attributes
  context = var.context
  name    = "firehose-delivery"

  role_description      = "IAM role for Firehose to deliver logs to S3 and invoke Lambda"
  policy_document_count = 1
  policy_documents      = [data.aws_iam_policy_document.firehose_permissions.json]

  # Allow Firehose service to assume this role
  assume_role_actions = ["sts:AssumeRole"]
  principals = {
    Service = ["firehose.amazonaws.com"]
  }
}

data "aws_iam_policy_document" "opensearch_ingestion_access" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
    resources = [var.logs_queue_arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion"
    ]
    resources = ["${var.logs_bucket_arn}/*"]
  }

  statement {
    effect = "Allow"
    actions = [
      # Collection-level access
      "aoss:APIAccessAll",
      "aoss:BatchGetCollection",

      # Index management
      "aoss:CreateIndex",
      "aoss:DeleteIndex",
      "aoss:UpdateIndex",
      "aoss:DescribeIndex",

      # Document operations
      "aoss:ReadDocument",
      "aoss:WriteDocument",

      # Collection items
      "aoss:CreateCollectionItems",
      "aoss:DeleteCollectionItems",
      "aoss:UpdateCollectionItems",
      "aoss:DescribeCollectionItems"
    ]
    resources = [
      "arn:aws:aoss:${local.region}:${local.account_id}:collection/${var.opensearch_collection_name}",
      "arn:aws:aoss:${local.region}:${local.account_id}:collection/${var.opensearch_collection_name}/*"
    ]
  }
}

module "opensearch_ingestion_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  # Label module attributes
  context = var.context
  name    = "opensearch-ingestion"

  role_description      = "IAM role for OpenSearch ingestion pipeline"
  policy_document_count = 1
  policy_documents      = [data.aws_iam_policy_document.opensearch_ingestion_access.json]

  # Allow OpenSearch service to assume this role
  assume_role_actions = ["sts:AssumeRole"]
  principals = {
    Service = ["osis-pipelines.amazonaws.com"]
  }
}

/**
 * Firehose Resources
 */

resource "aws_kinesis_firehose_delivery_stream" "opensearch_stream" {
  name        = module.firehose_label.id
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = module.firehose_role.arn
    bucket_arn = var.logs_bucket_arn
    prefix     = "firehose/"

    # Following AWS sample for optimal compression
    compression_format = "UNCOMPRESSED"

    # Lambda transformer for CloudWatch Logs
    processing_configuration {
      enabled = true

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = var.transformer_function_arn
        }
      }
    }

    # Buffering settings from AWS sample (60 seconds, 5 MB)
    buffering_interval = 60
    buffering_size     = 5

    # Enable CloudWatch logging
    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose_logs.name
      log_stream_name = "S3Delivery"
    }
  }

  timeouts {
    create = "45m"
    update = "45m"
    delete = "45m"
  }

  tags = module.firehose_label.tags

  depends_on = [
    aws_cloudwatch_log_group.firehose_logs
  ]
}

/**
 * OpenSearch Pipeline Resources
 */

resource "aws_osis_pipeline" "logs_pipeline" {
  pipeline_name = module.logs_pipeline_label.id

  min_units = 1
  max_units = 4

  pipeline_configuration_body = jsonencode({
    source = {
      sqs = {
        arn = var.logs_queue_url
      }
    }

    processor = {
      pipeline = {
        name = "logs-pipeline"
        config = {
          format = "json"
        }
      }
    }

    sink = {
      opensearch = {
        collection_endpoint = var.opensearch_collection_endpoint
        index               = module.logs_index_label.id
        role_arn            = module.opensearch_ingestion_role.arn
      }
    }
  })
}

/**
 * CloudFormation Resources
 */

resource "aws_cloudformation_stack_set" "log_subscription" {
  name             = module.logs_pipeline_label.id
  description      = "CloudWatch Logs subscription filter for OpenSearch ingestion"
  permission_model = "SERVICE_MANAGED"

  capabilities = ["CAPABILITY_NAMED_IAM"]

  auto_deployment {
    enabled                          = true
    retain_stacks_on_account_removal = false
  }

  operation_preferences {
    region_order = [local.region]

    failure_tolerance_percentage = 100
    max_concurrent_percentage    = 100
  }

  parameters = {
    FirehoseArn = aws_kinesis_firehose_delivery_stream.opensearch_stream.arn
  }

  template_body = file("${path.module}/files/cloudwatch-to-opensearch-member-account.yml")

  tags = module.logs_pipeline_label.tags
}

resource "aws_cloudformation_stack_set_instance" "org_deployment" {
  deployment_targets {
    organizational_unit_ids = var.organization_unit_deployment_targets
  }

  region         = local.region
  stack_set_name = aws_cloudformation_stack_set.log_subscription.name

  operation_preferences {
    failure_tolerance_percentage = 100
    max_concurrent_percentage    = 100
  }
}

/**
 * Cross-Account Resources
 */

data "aws_iam_policy_document" "opensearch_cross_account_access" {
  statement {
    effect = "Allow"
    actions = [
      "aoss:APIAccessAll"
    ]
    resources = [
      "arn:aws:aoss:${local.region}:${local.account_id}:collection/${var.opensearch_collection_name}"
    ]
  }
}

module "opensearch_cross_account_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  # Label module attributes
  context = var.context
  name    = "opensearch-cross-account"

  role_description      = "IAM role for cross-account OpenSearch access"
  policy_document_count = 1
  policy_documents      = [data.aws_iam_policy_document.opensearch_cross_account_access.json]

  # Allow member accounts to assume this role
  assume_role_actions = ["sts:AssumeRole"]
  principals = {
    AWS = ["arn:aws:iam::${local.account_id}:root"]
  }
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
