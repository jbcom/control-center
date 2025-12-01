output "metadata" {
  value = local.secret_data

  description = "Secrets metadata"
}

output "asset" {
  value = local.asset_arn

  description = "Special field holding the ARN of the asset matching the provided name, if any"
}

output "assets" {
  value = local.asset_data

  description = "Matched asset data"
}