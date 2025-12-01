module "delivery-stream-managed-private" {
  for_each = module.s3_buckets-private

  source = "../../kinesis/firehose-delivery-stream"

  bucket_name = each.value.bucket_id
  bucket_arn  = each.value.bucket_arn

  enabled = local.s3_buckets_private_config[each.key]["delivery_stream"]

  context = module.s3_buckets-private-context[each.key]["context"]
}

module "delivery-stream-managed-public" {
  for_each = module.s3_buckets-public

  source = "../../kinesis/firehose-delivery-stream"

  bucket_name = each.value.bucket_id
  bucket_arn  = each.value.bucket_arn

  enabled = local.s3_buckets_public_config[each.key]["delivery_stream"]

  context = module.s3_buckets-public-context[each.key]["context"]
}

locals {
  delivery_stream_private_data = {
    s3_buckets = {
      for bucket_name, stream_data in module.delivery-stream-managed-private : coalesce(local.configured_s3_buckets_private_only[bucket_name]["bucket_id"], bucket_name) => stream_data
    }
  }

  delivery_stream_public_data = {
    s3_buckets = {
      for bucket_name, stream_data in module.delivery-stream-managed-public : coalesce(local.configured_s3_buckets_public_only[bucket_name]["bucket_id"], bucket_name) => stream_data
    }
  }
}