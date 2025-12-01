locals {
  active_account_infrastructure = var.infrastructure[var.active_account]

  account_zones_data = local.active_account_infrastructure["zones"]

  zone_account_certificates = {
    for zone_name, zone_data in local.account_zones_data : zone_name => {
      for account_name, infrastructure_data in var.infrastructure : account_name => infrastructure_data["certificates"][zone_name] if lookup(infrastructure_data["certificates"], zone_name, {}) != {}
    }
  }
}

module "default" {
  for_each = local.zone_account_certificates

  source = "../certificate-validation-for-zone"

  zone_id = local.account_zones_data[each.key]["zone_id"]

  certificates = each.value
}