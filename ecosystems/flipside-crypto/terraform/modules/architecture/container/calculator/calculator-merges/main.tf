module "config_merge" {
  for_each = {
    for group_name, group_config in var.config : group_name => group_config if length(lookup(group_config, var.merge_config_key, [])) > 0
  }

  source = "../../../../utils/deepmerge"

  source_files = [
    for file_path in formatlist("%s/%s/%s.yaml", var.rel_to_root, var.merge_config_dir, each.value[var.merge_config_key]) : abspath(file_path)
  ]

  source_maps = [
    {
      for k, v in each.value : k => v if k != "merge"
    },
  ]
}

locals {
  merged_config = merge({
    for group_name, group_config in var.config : group_name => group_config if length(lookup(group_config, var.merge_config_key, [])) == 0
    }, {
    for group_name, merge_data in module.config_merge : group_name => merge_data["merged_maps"]
  })
}
