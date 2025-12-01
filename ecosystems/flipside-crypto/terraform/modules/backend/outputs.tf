output "backend_bucket_name" {
  value = module.tfstate_s3_bucket.bucket_id

  description = "S3 bucket ID"
}

output "backend_dynamodb_table" {
  value = aws_dynamodb_table.default.name

  description = "DynamoDB table name"
}