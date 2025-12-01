data "aws_iam_policy_document" "cloudtrail" {
  count = var.include_cloudtrail_policy ? 1 : 0

  statement {
    sid = "Allow CloudTrail to encrypt logs"
    principals {
      identifiers = ["cloudtrail.amazonaws.com"]
      type        = "Service"
    }
    resources = ["*"]
    actions   = ["kms:GenerateDataKey*"]
    condition {
      test     = "StringLike"
      values   = formatlist("arn:aws:cloudtrail:*:%s:trail/*", local.account_ids)
      variable = "kms:EncryptionContext:aws:cloudtrail:arn"
    }
  }

  statement {
    sid = "Allow CloudTrail to describe key"
    principals {
      identifiers = ["cloudtrail.amazonaws.com"]
      type        = "Service"
    }
    actions   = ["kms:DescribeKey"]
    resources = ["*"]
  }
}
