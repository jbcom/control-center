resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  force_destroy = true
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id = "expiration-after-1-day"

    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days                         = 1
      expired_object_delete_marker = true
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}
