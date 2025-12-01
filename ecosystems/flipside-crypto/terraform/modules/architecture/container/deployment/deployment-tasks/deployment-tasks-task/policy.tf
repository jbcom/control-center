locals {
  task_policy_documents = concat([
    data.aws_iam_policy_document.fluentbit_policy.json,
    ], module.task_secrets.policy_documents,
    data.aws_iam_policy_document.efs_policy_document.*.json,
    local.task_permissions_config["policy_document"] != {} ? [
      jsonencode(var.task_config["permissions"]["policy_document"]),
  ] : [])
}

module "task_policy" {
  source  = "cloudposse/iam-policy/aws"
  version = "2.0.2"

  attributes = ["task"]

  iam_policy_enabled = length(local.task_policy_documents) > 0

  iam_source_policy_documents = local.task_policy_documents

  context = local.task_context
}