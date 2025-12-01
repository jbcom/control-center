locals {
  legacy_resources_data = lookup(var.context["legacy_infrastructure"], local.json_key, {})

  unmanaged_resources_data = {
    access_logs = {
      (local.default_access_logs_bucket_name) = local.default_access_logs_bucket_data
    }

    s3_buckets = local.unmanaged_s3_bucket_data
  }
}