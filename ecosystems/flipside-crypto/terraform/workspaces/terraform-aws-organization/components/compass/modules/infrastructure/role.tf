module "copilot_execution_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.19.0"

  attributes = ["copilot-execution"]

  enabled = true

  policy_description = "Allow Copilot execution"
  role_description   = "Role for Copilot to assume"

  principals = {
    AWS = [
      local.compass_assume_role_arn,
    ]
  }

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AdministratorAccess",
  ]

  policy_document_count = 0

  context = var.context
}
