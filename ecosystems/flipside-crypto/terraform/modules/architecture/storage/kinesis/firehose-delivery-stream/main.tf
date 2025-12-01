data "aws_iam_policy_document" "default" {
  count = var.enabled ? 1 : 0

  statement {
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject",
    ]
    resources = [
      var.bucket_arn,
      "${var.bucket_arn}/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:*:*:*"
    ]
  }
}

module "delivery_stream_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  name         = var.bucket_name
  use_fullname = false
  attributes   = ["delivery", "stream"]
  enabled      = var.enabled

  policy_description = "Kinesis delivery stream policy"
  role_description   = "Kinesis delivery stream role"

  principals = {
    Service = ["firehose.amazonaws.com"]
  }

  policy_documents = data.aws_iam_policy_document.default.*.json

  context = var.context
}

resource "aws_kinesis_firehose_delivery_stream" "default" {
  count = var.enabled ? 1 : 0

  name        = var.bucket_name
  destination = "s3"

  s3_configuration {
    role_arn        = module.delivery_stream_role.arn
    bucket_arn      = var.bucket_arn
    buffer_size     = 1
    buffer_interval = 60

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/kinesisfirehose/${var.bucket_name}"
      log_stream_name = "S3Delivery"
    }
  }

  tags = merge(var.context.tags, {
    Name = var.bucket_name
  })
}