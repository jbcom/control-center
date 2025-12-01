module "delivery-stream-unmanaged" {
  for_each = local.unmanaged_s3_bucket_data

  source = "../../kinesis/firehose-delivery-stream"

  bucket_name = each.value["bucket_id"]
  bucket_arn  = each.value["bucket_arn"]

  enabled = local.s3_buckets_unmanaged_config[each.key]["delivery_stream"]

  context = var.context
}

locals {
  unmanaged_bucket_delivery_stream_data = {
    s3_buckets = {
      for bucket_name, stream_data in module.delivery-stream-unmanaged : bucket_name => stream_data
    }
  }
}