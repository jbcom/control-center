output "delivery_stream_name" {
  value = join("", aws_kinesis_firehose_delivery_stream.default.*.name)

  description = "Delivery stream name"
}

output "delivery_stream_arn" {
  value = join("", aws_kinesis_firehose_delivery_stream.default.*.arn)

  description = "Delivery stream arn"
}