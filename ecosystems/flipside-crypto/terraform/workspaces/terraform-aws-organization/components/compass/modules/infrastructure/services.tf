module "service_manifest_merge" {
  for_each = local.service_manifests_config

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/utils/deepmerge"

  source_maps = concat(local.base_manifests, [
    each.value,
    yamldecode(templatefile("${path.module}/templates/manifests/service.yml", {
      account_id         = local.account_id
      region             = local.region
      service_name       = each.key
      efs_filesystem_ids = local.efs_filesystem_ids
      dd_tags            = local.dd_tags
    }))
  ])
}

module "service_manifest_write" {
  for_each = module.service_manifest_merge

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/os/os-update-and-record-file"

  yaml_data = yamlencode(each.value.merged_maps)

  file_path = "copilot/${each.key}/manifest.yml"

  checksum = timestamp()

  log_file_name = "service-manifest-${each.key}.log"
}

locals {
  # Define addon sets
  all_addons = fileset("${var.rel_to_root}/addons", "*.yml")
  lb_addons  = toset(["waf.yml"])

  # Create service addon mappings based on service type
  service_addons = merge(
    # Non-LB services get all addons except lb_addons
    merge([
      for service_name, config in local.service_manifests_config : {
        for addon in setsubtract(local.all_addons, local.lb_addons) :
        "${service_name}/addons/${addon}" => file("${var.rel_to_root}/addons/${addon}")
      }
    ]...),
    # LB services get all addons
    merge([
      for service_name, config in local.service_manifests_config :
      try(config.type, "") == "Load Balanced Web Service" ? {
        for addon in local.lb_addons :
        "${service_name}/addons/${addon}" => file("${var.rel_to_root}/addons/${addon}")
      } : {}
    ]...)
  )
}

resource "local_sensitive_file" "service_addon_file" {
  for_each = local.service_addons
  filename = "${var.rel_to_root}/copilot/${each.key}"
  content  = each.value
}

resource "local_sensitive_file" "service_overrides_file" {
  for_each = merge(flatten([
    for service_name, _ in local.service_manifests_config : [
      for file_name in fileset("${var.rel_to_root}/overrides/services", "*.yml") : {
        "${service_name}/overrides/${file_name}" = file("${var.rel_to_root}/overrides/services/${file_name}")
      }
    ]
  ])...)

  filename = "${var.rel_to_root}/copilot/${each.key}"
  content  = each.value
}
