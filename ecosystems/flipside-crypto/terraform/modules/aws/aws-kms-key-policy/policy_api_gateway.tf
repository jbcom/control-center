data "aws_iam_policy_document" "api_gateway" {
  count = var.include_api_gateway_policy ? 1 : 0

  statement {
    sid = "Allow API Gateway to use this key"
    principals {
      identifiers = ["apigateway.amazonaws.com"]
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
    for_each = length(var.api_gateway_api_ids) > 0 ? [1] : []
    content {
      sid = "Allow specific API Gateway APIs to use this key"
      principals {
        identifiers = formatlist(
          "arn:aws:iam::%s:role/apigateway-service-role-%s",
          [for api_id in var.api_gateway_api_ids : split(":", api_id)[4]],
          var.api_gateway_api_ids
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
    }
  }
}
