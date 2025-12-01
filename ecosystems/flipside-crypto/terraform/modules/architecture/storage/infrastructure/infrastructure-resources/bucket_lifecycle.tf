module "private_bucket_lifecycle" {
  for_each = module.s3_buckets-private

  source = "../../s3/bucket-lifecycle"

  bucket_name = coalesce(each.value.bucket_id, each.key)

  config = merge(local.s3_buckets_private_config[each.key], {
    enabled = local.s3_buckets_private_config[each.key]["enabled"] && local.s3_buckets_private_config[each.key]["managed"]
  })

  depends_on = [
    module.s3_buckets-private,
  ]
}

module "public_bucket_lifecycle" {
  for_each = module.s3_buckets-public

  source = "../../s3/bucket-lifecycle"

  bucket_name = coalesce(each.value.bucket_id, each.key)

  config = merge(local.s3_buckets_public_config[each.key], {
    enabled = local.s3_buckets_public_config[each.key]["enabled"] && local.s3_buckets_public_config[each.key]["managed"]
  })

  depends_on = [
    module.s3_buckets-public,
  ]
}