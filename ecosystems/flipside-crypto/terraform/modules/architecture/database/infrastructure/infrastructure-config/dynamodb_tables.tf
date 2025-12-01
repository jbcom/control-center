locals {
  dynamodb_tables_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  dynamodb_tables_denylist = [
  ]
}

module "dynamodb_tables-defaults" {
  for_each = local.infrastructure_data["dynamodb_tables"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

      }, try(var.infrastructure_account_defaults["dynamodb_tables"][json_key], {}))

      base_data = {}

      override_data = {
      }

      required = [
      ]
    } if contains(local.dynamodb_tables_allowlist, json_key) && !contains(local.dynamodb_tables_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/dynamodb_tables.json"

  log_file_path = "${local.log_file_path}/dynamodb_tables/${each.key}"
}

locals {
  dynamodb_tables_config = {
    for module_name, module_data in module.dynamodb_tables-defaults : module_name => module_data["cycles"]
  }
}
