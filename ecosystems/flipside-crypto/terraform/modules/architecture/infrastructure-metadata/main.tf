module "organization_metadata" {
  source = "git@github.com:FlipsideCrypto/terraform-organization.git//modules/organization-metadata"
}

module "dns_metadata" {
  source = "git@github.com:FlipsideCrypto/dns-architecture.git//modules/infrastructure/infrastructure-metadata"
}

module "database_metadata" {
  source = "git@github.com:FlipsideCrypto/database-architecture.git//modules/infrastructure/infrastructure-metadata"
}

module "storage_metadata" {
  source = "git@github.com:FlipsideCrypto/storage-architecture.git//modules/infrastructure/infrastructure-metadata"
}

module "metadata" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/deepmerge"

  source_maps = [
    module.dns_metadata.metadata,
    module.database_metadata.metadata,
    module.storage_metadata.metadata,
  ]
}

locals {
  environment_name = var.infrastructure_environment != null ? var.infrastructure_environment : lookup(var.context, "environment", null)

  organization_data = module.organization_metadata.metadata
}

module "infrastructure_data" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/deepmerge"

  source_maps = [
    module.dns_metadata.infrastructure,
    module.database_metadata.infrastructure,
    module.storage_metadata.infrastructure,
  ]
}

module "docs" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/deepmerge"

  source_maps = [
    module.dns_metadata.docs,
    module.database_metadata.docs,
    module.storage_metadata.docs,
  ]
}

locals {
  infrastructure_account = coalesce(var.infrastructure_account, try(var.account_map[local.environment_name], null), local.organization_data["networked_accounts"][local.account_id]["json_key"])

  infrastructure_data = module.infrastructure_data.merged_maps

  dns_zones_flattened_view = merge(flatten([
    for _, infrastructure_data in local.infrastructure_data : [
      for zone_name, zone_data in lookup(infrastructure_data, "zones", {}) : {
        (zone_name) = zone_data
      } if zone_data["public"]
    ]
  ])...)

  dns_architecture_view = {
    for zone_name, zone_data in local.dns_zones_flattened_view : zone_name => merge(zone_data, {
      certificates = {
        for json_key, infrastructure_data in local.infrastructure_data : json_key => infrastructure_data["certificates"][zone_name] if try(infrastructure_data["certificates"][zone_name], {}) != {}
      }
    })
  }

  views_data = {
    dns = local.dns_architecture_view
  }

  account_infrastructure_data = lookup(local.infrastructure_data, local.infrastructure_account, {})

  docs_data = module.docs.merged_maps
}

data "assert_test" "infrastructure_contains_category" {
  count = var.category_name != null ? 1 : 0

  test = contains(keys(local.account_infrastructure_data), var.category_name)

  throw = "Category '${var.category_name}' not in the infrastructure data: ${join(", ", keys(local.account_infrastructure_data))}"
}

locals {
  asset_data = flatten([
    try(local.account_infrastructure_data[var.asset_name], [
      for _, asset_data in lookup(local.account_infrastructure_data, var.category_name, {}) : asset_data if alltrue(var.matchers != {} ? [
        for k, v in var.matchers : (lookup(asset_data, k, null) == v)
      ] : [true])
    ], [])
  ])
}

data "assert_test" "infrastructure_contains_expected_assets" {
  count = var.expected_assets > 0 ? 1 : 0

  test = length(local.asset_data) == var.expected_assets

  throw = "Expected ${var.expected_assets} asset(s), found ${length(local.asset_data)} asset(s)\nAsset(s): ${yamlencode(local.asset_data)}"
}