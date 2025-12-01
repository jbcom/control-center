module "data" {
  for_each = var.config

  source = "../../../../utils/deepmerge"

  source_maps = [
    {
      for k, v in each.value[var.data_key] : k => v if k != var.environments_key
    },
    try(each.value[var.data_key][var.environments_key][var.environment_name], {}),
  ]
}
