data "aws_iam_policy_document" "s3" {
  count = var.include_s3_policy ? 1 : 0

  statement {
    sid = "Allow S3 to use this key"
    principals {
      identifiers = ["s3.amazonaws.com"]
      type        = "Service"
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(var.s3_bucket_arns) > 0 ? [1] : []
    content {
      sid = "Allow specific S3 buckets to use this key"
      principals {
        identifiers = formatlist(
          "arn:aws:iam::%s:role/aws-service-role/s3.amazonaws.com/AWSServiceRoleForS3",
          [for bucket in var.s3_bucket_arns : data.aws_caller_identity.current.account_id]
        )
        type = "AWS"
      }
      actions = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ]
      resources = ["*"]
      condition {
        test     = "StringEquals"
        variable = "s3:ResourceAccount"
        values   = [data.aws_caller_identity.current.account_id]
      }
      condition {
        test     = "ArnLike"
        variable = "s3:bucket-name"
        values   = [for arn in var.s3_bucket_arns : element(split(":", arn), 5)]
      }
    }
  }
}
