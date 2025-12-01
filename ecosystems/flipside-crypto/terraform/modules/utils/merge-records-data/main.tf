module "records_category_merge" {
  for_each = var.record_categories

  source = "../deepmerge"

  source_directories = {
    (abspath(each.value["records_path"])) = each.value["pattern"]
  }

  ordered = var.ordered_records_merge
}

locals {
  raw_records_data = concat([
    var.records,
    ], [
    for category_name, category_data in module.records_category_merge : {
      (category_name) = category_data["merged_maps"]
    }
  ])
}

module "records_merge" {
  source = "../deepmerge"

  source_maps = local.raw_records_data

  source_files = [
    for file_path in var.record_files : abspath(file_path) if fileexists(abspath(file_path))
  ]

  source_directories = {
    for file_path, file_glob in var.record_directories : abspath(file_path) => file_glob
  }

  nest_data_under_key = var.nest_records_under_key

  ordered = var.ordered_records_merge

  allowlist = var.allowlist
  denylist  = var.denylist

  verbose = var.verbose

  log_file_name = "merge-records.log"
}

locals {
  records_data = module.records_merge.merged_maps
}