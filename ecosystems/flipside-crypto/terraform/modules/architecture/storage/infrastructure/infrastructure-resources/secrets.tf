locals {
  spokes_data = var.context["networks"]

  authorized_execution_role_arns = compact(distinct([
    for _, spoke_data in local.spokes_data : spoke_data["execution_role_arn"]
  ]))
}

data "aws_iam_policy_document" "secret_policy" {
  count = var.secret_policy == null ? 1 : 0

  statement {
    principals {
      type        = "AWS"
      identifiers = local.authorized_execution_role_arns
    }

    actions = [
      "secretsmanager:*",
    ]

    resources = ["*"]
  }
}

locals {
  secret_policy_json = coalesce(var.secret_policy, data.aws_iam_policy_document.secret_policy.0.json)
}
