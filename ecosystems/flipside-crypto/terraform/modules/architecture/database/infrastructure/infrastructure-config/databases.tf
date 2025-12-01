locals {
  databases_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  databases_denylist = [
  ]
}

module "databases-defaults" {
  for_each = local.infrastructure_data["databases"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        admin_user = replace(title(replace(replace(each.key, "-", " "), "_", " ")), " ", "")

        autoscaling_enabled = account_data["environment"] != "stg" ? true : false

        autoscaling_max_capacity = account_data["environment"] != "stg" ? 9 : 1

        cluster_size = account_data["environment"] != "stg" ? 3 : 1

        db_name = replace(title(replace(replace(each.key, "-", " "), "_", " ")), " ", "")

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

        performance_insights_retention_period = account_data["environment"] != "stg" ? 731 : 7

        retention_period = account_data["environment"] != "stg" ? 30 : 7

        skip_final_snapshot = account_data["environment"] != "stg" ? false : true

      }, try(var.infrastructure_account_defaults["databases"][json_key], {}))

      base_data = {}

      override_data = {
      }

      required = [
      ]
    } if contains(local.databases_allowlist, json_key) && !contains(local.databases_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/databases.json"

  log_file_path = "${local.log_file_path}/databases/${each.key}"
}

locals {
  databases_config = {
    for module_name, module_data in module.databases-defaults : module_name => module_data["cycles"]
  }
}
