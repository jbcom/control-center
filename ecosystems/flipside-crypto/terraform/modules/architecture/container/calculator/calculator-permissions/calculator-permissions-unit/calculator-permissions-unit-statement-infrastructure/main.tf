module "statement_infrastructure_asset_data" {
  count = length(var.infrastructure)

  source = "../../../../../../infrastructure/infrastructure-metadata"

  category_name = var.infrastructure[count.index].category

  matchers = var.infrastructure[count.index].matchers

  account_map = var.infrastructure[count.index].accounts

  data_key = var.infrastructure[count.index].key

  expected_assets = 1

  infrastructure_environment = var.environment_name
  infrastructure_account     = var.account_json_key

  context = var.context
}

locals {
  statement_infrastructure_asset_arns = distinct(compact(flatten(module.statement_infrastructure_asset_data.*.asset)))
}
