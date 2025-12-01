locals {
  access_logs_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  access_logs_denylist = [
  ]
}

module "access_logs-defaults" {
  for_each = local.infrastructure_data["access_logs"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

      }, try(var.infrastructure_account_defaults["access_logs"][json_key], {}))

      base_data = {}

      override_data = {
      }

      required = [
      ]
    } if contains(local.access_logs_allowlist, json_key) && !contains(local.access_logs_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/access_logs.json"

  log_file_path = "${local.log_file_path}/access_logs/${each.key}"
}

locals {
  access_logs_config = {
    for module_name, module_data in module.access_logs-defaults : module_name => module_data["cycles"]
  }
}
