data "aws_iam_policy_document" "cloudwatch_logs" {
  count = var.include_cloudwatch_logs_policy ? 1 : 0

  statement {
    sid = "Allow CloudWatch logs to be used with this key"
    principals {
      identifiers = ["logs.${local.region}.amazonaws.com"]
      type        = "Service"
    }
    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]
    resources = ["*"]
  }
}
