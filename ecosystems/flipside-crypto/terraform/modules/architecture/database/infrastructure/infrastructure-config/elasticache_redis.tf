locals {
  elasticache_redis_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  elasticache_redis_denylist = [
  ]
}

module "elasticache_redis-defaults" {
  for_each = local.infrastructure_data["elasticache_redis"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        cluster_mode_enabled = account_data["environment"] != "stg" ? true : false

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

      }, try(var.infrastructure_account_defaults["elasticache_redis"][json_key], {}))

      base_data = {}

      override_data = {
      }

      required = [
      ]
    } if contains(local.elasticache_redis_allowlist, json_key) && !contains(local.elasticache_redis_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/elasticache_redis.json"

  log_file_path = "${local.log_file_path}/elasticache_redis/${each.key}"
}

locals {
  elasticache_redis_config = {
    for module_name, module_data in module.elasticache_redis-defaults : module_name => module_data["cycles"]
  }
}
