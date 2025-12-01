module "this" {
  for_each = var.cycles

  source = "../defaults-merge"

  source_map = var.source_map

  defaults = each.value.defaults

  base = each.value.base_data

  overrides = each.value.override_data

  defaults_file_path = var.defaults_file_path

  allow_empty_values = var.allow_empty_values

  allowlist_key   = var.allowlist_key
  allowlist_value = lookup(each.value, "allowlist_value", each.key)

  log_file_name = "${each.key}.log"
  log_file_path = var.log_file_path
}