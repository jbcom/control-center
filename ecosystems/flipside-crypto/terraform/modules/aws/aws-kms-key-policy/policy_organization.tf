data "aws_iam_policy_document" "organization" {
  count = var.include_organization_policy ? 1 : 0

  statement {
    sid = "Allow organization access to the key"

    principals {
      identifiers = ["*"]
      type        = "AWS"
    }

    actions = var.iam_statement_actions

    resources = ["*"]

    condition {
      test = "StringEquals"
      values = [
        local.organization_id,
      ]

      variable = "aws:PrincipalOrgID"
    }
  }
}
