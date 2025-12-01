module "permissions" {
  for_each = var.config

  source = "./calculator-permissions-unit"

  environment_name = var.environment_name

  account_data = var.account_data

  permissions = each.value["permissions"]

  context = var.context

  rel_to_root = var.rel_to_root
}
