data "aws_iam_policy_document" "autoscaling" {
  count = var.include_autoscaling_policy ? 1 : 0

  statement {
    sid = "Allow autoscaling use of the customer managed key"

    principals {
      identifiers = local.autoscaling_identifiers
      type        = "AWS"
    }

    actions = var.iam_statement_actions

    resources = ["*"]
  }

  statement {
    sid = "Allow attachment of persistent resources for autoscaling"

    principals {
      identifiers = local.autoscaling_identifiers
      type        = "AWS"
    }

    actions = [
      "kms:CreateGrant",
    ]

    resources = ["*"]

    condition {
      test     = "Bool"
      values   = ["true"]
      variable = "kms:GrantIsForAWSResource"
    }
  }
}
