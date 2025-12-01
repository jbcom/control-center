locals {
  source_maps   = jsonencode(var.source_maps)
  log_file_name = var.log_file_name != "" ? var.log_file_name : "${md5(local.source_maps)}.log"
  log_file_path = var.log_file_path != "" ? var.log_file_path : "${path.root}/logs/multi-merges"
  log_file      = "${local.log_file_path}/${local.log_file_name}"
  merged_maps   = jsondecode(base64decode(data.external.merge.result["merged_maps"]))
}

data "external" "merge" {
  program = ["python", "${path.module}/bin/merge.py"]

  query = {
    source_maps        = jsonencode(var.source_maps)
    reject_enumerables = var.reject_enumerables
    reject_empty       = var.reject_empty
    log_file           = local.log_file
  }
}
