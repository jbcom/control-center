data "aws_iam_policy_document" "lambda" {
  count = var.include_lambda_policy ? 1 : 0

  statement {
    sid = "Allow Lambda to use this key"
    principals {
      identifiers = ["lambda.amazonaws.com"]
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
    for_each = length(var.lambda_function_arns) > 0 ? [1] : []
    content {
      sid = "Allow specific Lambda functions to use this key"
      principals {
        identifiers = formatlist(
          "arn:aws:iam::%s:role/%s",
          [for fn in var.lambda_function_arns : split(":", fn)[4]],
          [for fn in var.lambda_function_arns : "lambda_exec_${split(":", fn)[6]}"]
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
