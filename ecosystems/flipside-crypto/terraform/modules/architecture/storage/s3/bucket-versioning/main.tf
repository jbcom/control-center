resource "aws_s3_bucket_versioning" "default" {
  count = var.enabled ? 1 : 0

  bucket = var.bucket_name

  versioning_configuration {
    status = "Enabled"
  }
}