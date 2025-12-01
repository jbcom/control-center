output "s3_arn" {
  value = aws_s3_bucket.s3_bucket.arn
}

output "s3_id" {
  value = aws_s3_bucket.s3_bucket.id
}

output "s3_bucket" {
  value = aws_s3_bucket.s3_bucket.bucket
}


output "sf_user_id" {
  value = aws_iam_access_key.sfuseraccesskey.id
}

output "sf_user_secret" {
  value = aws_iam_access_key.sfuseraccesskey.secret
}

output "sqs_4_snowpipe" {
  value = snowflake_pipe.snowpipe.notification_channel
}

output "kinesis_arn" {
  value = aws_kinesis_firehose_delivery_stream.stream.arn
}

output "kinesis_name" {
  value = aws_kinesis_firehose_delivery_stream.stream.name
}

output "ssm_arn_firehose_delivery_stream" {
  value = aws_ssm_parameter.firehose_stream_name.arn
}
