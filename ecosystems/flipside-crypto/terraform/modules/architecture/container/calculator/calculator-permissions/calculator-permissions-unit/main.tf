module "statement_infrastructure_asset_data" {
  for_each = {
    for sid, statement_data in var.permissions.statements : sid => statement_data["infrastructure"] if length(statement_data["infrastructure"]) > 0
  }

  source = "./calculator-permissions-unit-statement-infrastructure"

  environment_name = var.environment_name

  account_json_key = var.account_data.json_key

  infrastructure = each.value

  context = var.context
}

data "aws_iam_policy_document" "default" {
  source_policy_documents   = formatlist("%s/%s/%s", var.rel_to_root, var.policies_config_dir, var.permissions.source_policy_documents)
  override_policy_documents = formatlist("%s/%s/%s", var.rel_to_root, var.policies_config_dir, var.permissions.override_policy_documents)

  dynamic "statement" {
    for_each = var.permissions.statements

    content {
      sid = statement.key

      actions   = statement.value.actions
      effect    = statement.value.effect
      resources = distinct(flatten(concat(statement.value.resources, length(statement.value.infrastructure) > 0 ? module.statement_infrastructure_asset_data[statement.key].infrastructure : [])))

      dynamic "condition" {
        for_each = length(statement.value.conditions) > 0 ? range(length(statement.value.conditions)) : []

        content {
          test     = statement.value.conditions[condition.key].test
          values   = statement.value.conditions[condition.key].values
          variable = statement.value.conditions[condition.key].variable
        }
      }
    }
  }
}

locals {
  policy_document_raw = jsondecode(data.aws_iam_policy_document.default.json)
  policy_document_base = {
    exists = local.policy_document_raw
    empty  = {}
  }

  policy_document_key = keys(local.policy_document_raw) == ["Version"] ? "empty" : "exists"
  policy_document     = local.policy_document_base[local.policy_document_key]

  managed_policy_arn_template = "arn:aws:iam::${var.account_data.id}:policy/%s"

  policy_arns = [
    for policy_name, policy_config in var.permissions.policies : (startswith(policy_name, "arn:") ? policy_name : (policy_config["AwsManaged"] ? "arn:aws:iam::aws:policy/${policy_name}" : local.managed_policy_arn_template))
  ]
}
