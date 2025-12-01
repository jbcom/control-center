module "default" {
  for_each = var.config

  source = "./container-networking-unit"

  identifier = "${var.identifier}-${each.key}"

  config = each.value
}
