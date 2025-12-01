output "metadata" {
  value = local.infrastructure_data

  description = "Infrastructure metadata"
}

output "infrastructure" {
  value = local.base_infrastructure_data

  description = "Infrastructure data with no merging"
}

output "cross_account" {
  value = local.cross_account_merge_allowmap

  description = "Categories of infrastructure and their cross account merge status"
}

output "docs" {
  value = local.docs_data

  description = "CloudPosse module docs"
}