locals {
  dynamodb_principals = distinct(concat([
    "arn:aws:iam::${local.primary_account_id}:root",
  ], var.dynamodb_principals, var.enable_dynamodb_for_all_grantees ? var.grantees : []))
}

data "aws_iam_policy_document" "dynamodb" {
  count = var.include_dynamodb_policy && length(local.dynamodb_principals) > 0 ? 1 : 0

  statement {
    sid = "Allow access through Amazon DynamoDB for all principals in the account that are authorized to use Amazon DynamoDB"

    principals {
      identifiers = local.dynamodb_principals
      type        = "AWS"
    }

    actions = var.iam_statement_actions

    resources = ["*"]

    condition {
      test     = "StringLike"
      values   = ["dynamodb.*.amazonaws.com"]
      variable = "kms:ViaService"
    }
  }
}
