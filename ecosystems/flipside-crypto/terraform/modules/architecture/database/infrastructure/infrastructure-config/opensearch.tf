locals {
  opensearch_allowlist = coalescelist([
  ], keys(local.networked_accounts_data))

  opensearch_denylist = [
  ]
}

module "opensearch-defaults" {
  for_each = local.infrastructure_data["opensearch"]

  source = "../../../../../../terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
        account_id = account_data["id"]

        advanced_security_options_master_user_name = replace(title(replace(replace(each.key, "-", " "), "_", " ")), " ", "")

        execution_role_arn = account_data["execution_role_arn"]

        name = each.key

      }, try(var.infrastructure_account_defaults["opensearch"][json_key], {}))

      base_data = {}

      override_data = {
        create_iam_service_linked_role = false
      }

      required = [
      ]
    } if contains(local.opensearch_allowlist, json_key) && !contains(local.opensearch_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "${path.module}/defaults/opensearch.json"

  log_file_path = "${local.log_file_path}/opensearch/${each.key}"
}

locals {
  opensearch_config = {
    for module_name, module_data in module.opensearch-defaults : module_name => module_data["cycles"]
  }
}
