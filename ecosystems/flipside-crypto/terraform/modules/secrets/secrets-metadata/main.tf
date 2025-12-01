locals {
  environment_name = var.secret_environment != null ? var.secret_environment : lookup(var.context, "environment", null)

  secret_account = coalesce(var.secret_account, try(var.account_map[local.environment_name], null), var.context["networked_accounts"][local.account_id]["json_key"])

  secret_data = jsondecode(file("${path.module}/files/metadata.json"))

  account_secret_data = lookup(local.secret_data, local.secret_account, {})

  account_secret_category_data = try(local.account_secret_data[var.category_name], {})

  base_asset_data = {
    with_name = {
      (coalesce(var.asset_name, "null")) = try(local.account_secret_category_data[var.asset_name], "")
    }

    without_name = {
      for secret_key, secret_arn in local.account_secret_category_data : secret_key => secret_arn if anytrue(length(var.matchers) > 0 ? [
        for matcher in var.matchers : startswith(secret_key, matcher)
      ] : [true])
    }
  }

  asset_data_key = var.asset_name != null ? "with_name" : "without_name"

  asset_data = local.base_asset_data[local.asset_data_key]
  asset_arn  = lookup(local.asset_data, var.asset_name, "")
}

data "assert_test" "secrets_contain_expected_asset" {
  count = var.expected_assets > 0 && var.asset_name != null ? 1 : 0

  test = local.asset_arn != ""

  throw = "Did not find an asset ARN for ${var.asset_name}\nAsset(s):\n\n${yamlencode(local.asset_data)}"
}

data "assert_test" "secrets_contain_expected_assets" {
  count = var.expected_assets > 0 ? 1 : 0

  test = length(keys(local.asset_data)) == var.expected_assets

  throw = "Expected ${var.expected_assets} asset(s), found ${length(local.asset_data)} asset(s)\nAsset(s): ${yamlencode(local.asset_data)}"
}
