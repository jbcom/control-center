locals {
  environment_name = var.infrastructure_environment != null ? var.infrastructure_environment : lookup(var.context, "environment", null)

  account_data           = var.context["networked_accounts"][local.account_id]
  infrastructure_account = coalesce(var.infrastructure_account, try(var.account_map[local.environment_name], null), local.account_data["json_key"])
}

module "infrastructure_asset_data" {
  source = "../../vault/vault-find-vault-secret"

  secret_name = var.asset_name

  secret_path_prefix = "infrastructure/${local.infrastructure_account}/${var.category_name}"

  matchers = var.matchers

  execution_role_arn = local.account_data["execution_role_arn"]

  log_file_name = var.log_file_name
}

locals {
  asset_data = try(module.infrastructure_asset_data.secret[var.data_key], module.infrastructure_asset_data.secret)
}
