locals {
  efs_filesystems_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  efs_filesystems_denylist = [
  ]
}

module "efs_filesystems-defaults" {
  for_each = local.infrastructure_data["efs_filesystems"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

        transition_to_ia = account_data["environment"] != "stg" ? ["AFTER_90_DAYS"] : ["AFTER_7_DAYS"]

      }, try(var.infrastructure_account_defaults["efs_filesystems"][json_key], {}))

      base_data = {}

      override_data = {
        private = true
        public  = false
      }

      required = [
      ]
    } if contains(local.efs_filesystems_allowlist, json_key) && !contains(local.efs_filesystems_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/efs_filesystems.json"

  log_file_path = "${local.log_file_path}/efs_filesystems/${each.key}"
}

locals {
  efs_filesystems_config = {
    for module_name, module_data in module.efs_filesystems-defaults : module_name => module_data["cycles"]
  }
}
