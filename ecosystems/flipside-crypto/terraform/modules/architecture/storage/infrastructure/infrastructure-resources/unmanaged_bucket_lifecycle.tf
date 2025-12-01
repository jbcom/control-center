module "unmanaged_bucket_versioning" {
  for_each = local.s3_buckets_unmanaged_config

  source = "../../s3/bucket-versioning"

  bucket_name = each.key

  enabled = each.value["versioning_enabled"] ? true : (each.value["max_days"] > 0 || each.value["max_noncurrent_days"] > 0 || each.value["transition_after"] > 0 || each.value["noncurrent_transition_after"] > 0)
}

module "unmanaged_bucket_lifecycle" {
  for_each = local.s3_buckets_unmanaged_config

  source = "../../s3/bucket-lifecycle"

  bucket_name = each.key

  config = each.value

  depends_on = [
    module.unmanaged_bucket_versioning,
  ]
}