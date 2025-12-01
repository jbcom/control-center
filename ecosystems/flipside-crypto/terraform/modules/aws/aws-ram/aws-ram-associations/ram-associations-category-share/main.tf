locals {
  ram_associations_data = var.context["ram_associations"]
}

module "asset" {
  for_each = var.config

  source = "./ram-associations-category-share-resource"

  resource_arn = var.infrastructure[each.key]["arn"]

  resource_share_arns = [
    for json_key in each.value.accounts : local.ram_associations_data[json_key]
  ]
}