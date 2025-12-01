data "aws_iam_policy_document" "this" {
  source_policy_documents = var.source_policy_documents
  override_policy_documents = concat(
    var.override_policy_documents,
    data.aws_iam_policy_document.autoscaling.*.json,
    data.aws_iam_policy_document.organization.*.json,
    data.aws_iam_policy_document.dynamodb.*.json,
    data.aws_iam_policy_document.cloudtrail.*.json,
    data.aws_iam_policy_document.cloudwatch_logs.*.json,
    data.aws_iam_policy_document.lambda.*.json,
    data.aws_iam_policy_document.api_gateway.*.json,
    data.aws_iam_policy_document.s3.*.json,
    data.aws_iam_policy_document.cloudfront.*.json
  )

  statement {
    sid     = "Allow accounts access to the key"
    actions = ["kms:*"]
    principals {
      identifiers = formatlist("arn:aws:iam::%s:root", local.account_ids)
      type        = "AWS"
    }
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = !var.authorize_all_in_account && length(var.grantees) > 0 ? [0] : []
    content {
      sid = "Allow grantees use of the key for encryption and decryption"
      principals {
        identifiers = var.grantees
        type        = "AWS"
      }
      actions   = var.iam_statement_actions
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.authorize_all_in_account ? [0] : []
    content {
      sid = "Allow account members use of the key for encryption and decryption"
      principals {
        identifiers = ["*"]
        type        = "AWS"
      }
      actions   = var.iam_statement_actions
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = toset(var.grantees)
    content {
      sid     = "Grant ${statement.value} access to the key"
      actions = var.grant_operations
      principals {
        type        = "AWS"
        identifiers = [statement.value]
      }
      resources = ["*"]
    }
  }
}

resource "aws_kms_key_policy" "default" {
  count  = var.kms_policy_enabled ? 1 : 0
  key_id = var.kms_key_id
  policy = data.aws_iam_policy_document.this.json
}
