output "metadata" {
  value = module.metadata.merged_maps

  description = "Infrastructure metadata"
}

output "infrastructure" {
  value = local.infrastructure_data

  description = "Raw infrastructure data"
}

output "asset" {
  value = try(one(local.asset_data), {})

  description = "Special field holding a singular found asset, or an empty map if more than one found asset"
}

output "assets" {
  value = local.asset_data

  description = "Matched asset data"
}

output "views" {
  value = local.views_data

  description = "Views data"
}

output "docs" {
  value = local.docs_data

  description = "Docs data"
}