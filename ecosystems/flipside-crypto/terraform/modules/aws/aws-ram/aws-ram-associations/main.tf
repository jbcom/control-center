module "category" {
  for_each = var.config

  source = "./ram-associations-category-share"

  config = each.value

  infrastructure = lookup(var.infrastructure, each.key, {})

  context = var.context
}