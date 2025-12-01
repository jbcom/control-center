locals {
  docs_data = jsondecode(file("${path.module}/files/docs.json"))

  cross_account_merge_allowmap = yamldecode(file("${path.module}/files/config.yaml"))

  base_infrastructure_data = jsondecode(file("${path.module}/files/infrastructure.json"))

  account_specific_infrastructure_categories = [
    for category_name, cross_account_merge_allowed in local.cross_account_merge_allowmap : category_name if !cross_account_merge_allowed
  ]

  account_specific_infrastructure_base_data = {
    for category_name in local.account_specific_infrastructure_categories : category_name => {
      for json_key, infrastructure_data in local.base_infrastructure_data : json_key => infrastructure_data[category_name]
    }
  }

  cross_account_infrastructure_base_data = [
    for json_key, infrastructure_data in local.base_infrastructure_data : {
      for category_name, category_data in infrastructure_data : category_name => category_data if local.cross_account_merge_allowmap[category_name]
    }
  ]
}

module "infrastructure_data" {
  source = "../../../../../../terraform/modules/utils/deepmerge"

  source_maps = concat(local.cross_account_infrastructure_base_data, [
    local.account_specific_infrastructure_base_data,
  ])
}

locals {
  infrastructure_data = module.infrastructure_data.merged_maps
}
