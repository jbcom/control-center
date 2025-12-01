locals {
  unmanaged_resources_data = {
    databases = {
      for asset_name, asset_data in local.configured_unmanaged_databases : asset_name => asset_data
    }
  }
}