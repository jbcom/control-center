locals {
  filtered_records_data = {
    for k, v in var.records : k => v if !contains(var.denylist, k) && (length(var.allowlist) == 0 || contains(var.allowlist, k))
  }
}