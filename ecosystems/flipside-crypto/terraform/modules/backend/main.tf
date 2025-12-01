module "tfstate_s3_bucket" {
  source  = "cloudposse/s3-bucket/aws"
  version = "4.10.0"

  bucket_name = var.backend_name

  force_destroy = true

  versioning_enabled = var.enable_versioning

  tags = var.tags
}

resource "aws_dynamodb_table" "default" {
  name           = local.dynamodb_table_name
  billing_mode   = var.billing_mode
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null

  # https://www.terraform.io/docs/backends/types/s3.html#dynamodb_table
  hash_key = "LockID"

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = merge(var.tags, {
    Name = local.dynamodb_table_name
  })
}