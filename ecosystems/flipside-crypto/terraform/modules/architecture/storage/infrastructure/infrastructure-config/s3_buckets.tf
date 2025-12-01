locals {
  s3_buckets_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  s3_buckets_denylist = [
  ]
}

module "s3_buckets-defaults" {
  for_each = local.infrastructure_data["s3_buckets"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

      }, try(var.infrastructure_account_defaults["s3_buckets"][json_key], {}))

      base_data = {}

      override_data = {
        store_access_key_in_ssm = true
      }

      required = [
      ]
    } if contains(local.s3_buckets_allowlist, json_key) && !contains(local.s3_buckets_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/s3_buckets.json"

  log_file_path = "${local.log_file_path}/s3_buckets/${each.key}"
}

locals {
  s3_buckets_config = {
    for module_name, module_data in module.s3_buckets-defaults : module_name => module_data["cycles"]
  }
}
