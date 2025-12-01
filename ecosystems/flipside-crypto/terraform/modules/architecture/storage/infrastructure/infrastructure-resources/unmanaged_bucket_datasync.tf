locals {
  unmanaged_bucket_datasync_target_buckets = {
    for bucket_name, bucket_data in local.unmanaged_s3_bucket_data : bucket_name => bucket_data if local.s3_buckets_unmanaged_config[bucket_name]["datasync"]
  }
}

module "datasync-s3-unmanaged" {
  for_each = local.unmanaged_s3_bucket_data

  source = "../../datasync/datasync-location/datasync-location-s3-bucket"

  config = local.s3_buckets_unmanaged_config[each.key]

  data = each.value

  role_arn  = local.datasync_s3_role_arns[each.key]
  role_name = local.datasync_s3_role_names[each.key]

  context = var.context
}

locals {
  unmanaged_bucket_datasync_data = {
    s3_buckets = {
      for bucket_name, sync_data in module.datasync-s3-unmanaged : bucket_name => sync_data
    }
  }
}