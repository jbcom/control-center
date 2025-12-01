/**
 * # Defaults-Merge
 *
 * An issue (https://github.com/hashicorp/terraform/issues/18413) prevents using defaults to merge optional maps / lists
 * This serves as a replacement for that until the issue is resolved
 */

locals {
  source_map_json    = jsonencode(var.source_map)
  source_map_md5     = md5(local.source_map_json)
  log_file_base_path = "${path.root}/logs/defaults"
  log_file_path      = "${local.log_file_base_path}/${trimprefix(var.log_file_path, local.log_file_base_path)}"
  log_file_name      = var.log_file_name != "" ? "${trimsuffix(var.log_file_name, ".log")}.log" : "${local.source_map_md5}.log"
  log_file           = "${local.log_file_path}/${local.log_file_name}"
}

data "external" "merge" {
  program = ["python", "${path.module}/bin/merge.py"]

  query = {
    source_map         = local.source_map_json
    defaults_file_path = var.defaults_file_path
    defaults           = jsonencode(var.defaults)
    base               = jsonencode(var.base)
    overrides          = jsonencode(var.overrides)
    allow_empty_values = var.allow_empty_values
    allowlist_key      = var.allowlist_key
    allowlist_value    = var.allowlist_value
    log_file           = local.log_file
  }
}

locals {
  results_data = jsondecode(base64decode(data.external.merge.result["merged_map"]))
}