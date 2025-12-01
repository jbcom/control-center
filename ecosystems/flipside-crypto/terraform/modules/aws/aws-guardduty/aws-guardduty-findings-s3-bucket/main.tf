locals {
  guardduty_config = var.context["guardduty"]["configuration"]
}

module "s3_bucket" {
  providers = {
    aws = aws.src
  }

  source  = "cloudposse/s3-bucket/aws"
  version = "4.10.0"

  bucket_name = local.guardduty_config.logging_acc_s3_bucket_name

  acl           = "private"
  force_destroy = true

  logging = {
    bucket_name = local.guardduty_config.s3_access_log_bucket_name
    prefix      = "log/"
  }

  versioning_enabled = true

  kms_master_key_arn = aws_kms_key.gd_key.arn
  sse_algorithm      = "aws:kms"

  lifecycle_configuration_rules = [
    {
      id      = "transition-objects-to-glacier-and-expire"
      enabled = var.s3_bucket_enable_object_transition_to_glacier

      transition = [
        {
          days          = var.s3_bucket_object_transition_to_glacier_after_days
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = var.s3_bucket_object_deletion_after_days
      }

      abort_incomplete_multipart_upload_days = null
      filter_and                             = null
      noncurrent_version_expiration          = null
      noncurrent_version_transition          = null
    }
  ]

  context = var.context
}

locals {
  bucket_data = module.s3_bucket
  bucket_arn  = local.bucket_data["bucket_arn"]
  bucket_id   = local.bucket_data["bucket_id"]
}

# GD Findings Bucket policy
data "aws_iam_policy_document" "bucket_pol" {
  statement {
    sid = "Allow PutObject"
    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${local.bucket_arn}/*"
    ]

    principals {
      type        = "Service"
      identifiers = ["guardduty.amazonaws.com"]
    }
  }

  statement {
    sid = "AWSBucketPermissionsCheck"
    actions = [
      "s3:GetBucketLocation",
      "s3:GetBucketAcl",
      "s3:ListBucket"
    ]

    resources = [
      local.bucket_arn
    ]

    principals {
      type        = "Service"
      identifiers = ["guardduty.amazonaws.com"]
    }
  }

  statement {
    sid    = "Deny unencrypted object uploads. This is optional"
    effect = "Deny"
    principals {
      type        = "Service"
      identifiers = ["guardduty.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "${local.bucket_arn}/*"
    ]
    condition {
      test     = "StringNotEquals"
      variable = "s3:x-amz-server-side-encryption"

      values = [
        "aws:kms"
      ]
    }
  }

  statement {
    sid    = "Deny incorrect encryption header. This is optional"
    effect = "Deny"
    principals {
      type        = "Service"
      identifiers = ["guardduty.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "${local.bucket_arn}/*"
    ]
    condition {
      test     = "StringNotEquals"
      variable = "s3:x-amz-server-side-encryption-aws-kms-key-id"

      values = [
        aws_kms_key.gd_key.arn
      ]
    }
  }

  statement {
    sid    = "Deny non-HTTPS access"
    effect = "Deny"
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    actions = [
      "s3:*"
    ]
    resources = [
      "${local.bucket_arn}/*"
    ]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"

      values = [
        "false"
      ]
    }
  }

  statement {
    sid    = "Access logs ACL check"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:GetBucketAcl"
    ]
    resources = [
      local.bucket_arn
    ]
  }

  statement {
    sid    = "Access logs write"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      local.bucket_arn,
      "${local.bucket_arn}/AWSLogs/*"
    ]
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"

      values = [
        "bucket-owner-full-control"
      ]
    }
  }
}

resource "aws_s3_bucket_policy" "gd_bucket_policy" {
  provider = aws.src

  bucket = local.bucket_id
  policy = data.aws_iam_policy_document.bucket_pol.json
}


