locals {
  infrastructure_raw_cycles = {
    access_logs = local.access_logs_config

    efs_filesystems = local.efs_filesystems_config

    s3_buckets = local.s3_buckets_config

  }

  infrastructure_raw_config = {
    for json_key, _ in local.networked_accounts_data : json_key => {
      for category_name, category_data in local.infrastructure_raw_cycles : category_name => {
        for module_name, module_cycles in category_data : module_name => module_cycles[json_key] if contains(keys(module_cycles), json_key)
      }
    }
  }

  infrastructure_config = {
    for json_key, category_data in local.infrastructure_raw_config : json_key => {
      for category_name, module_data in category_data : category_name => {
        for module_name, module_config in module_data : module_name => module_config if contains(module_config["accounts"], json_key)
      }
    }
  }
}
