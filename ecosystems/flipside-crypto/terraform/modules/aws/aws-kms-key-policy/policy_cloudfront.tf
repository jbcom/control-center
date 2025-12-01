data "aws_iam_policy_document" "cloudfront" {
  count = var.include_cloudfront_policy ? 1 : 0

  statement {
    sid = "Allow CloudFront to use this key"
    principals {
      identifiers = ["cloudfront.amazonaws.com"]
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
    for_each = length(var.cloudfront_distribution_ids) > 0 ? [1] : []
    content {
      sid = "Allow specific CloudFront distributions to use this key"
      principals {
        identifiers = ["cloudfront.amazonaws.com"]
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
      condition {
        test     = "StringEquals"
        variable = "aws:SourceArn"
        values   = formatlist("arn:aws:cloudfront::%s:distribution/%s", [for id in var.cloudfront_distribution_ids : data.aws_caller_identity.current.account_id], var.cloudfront_distribution_ids)
      }
    }
  }

  # Allow Lambda@Edge to use this key
  dynamic "statement" {
    for_each = var.include_lambda_edge_policy ? [1] : []
    content {
      sid = "Allow Lambda@Edge to use this key"
      principals {
        identifiers = ["edgelambda.amazonaws.com"]
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
  }
}
