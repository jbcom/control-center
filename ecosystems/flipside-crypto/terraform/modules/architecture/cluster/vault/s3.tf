data "aws_iam_policy_document" "s3_trust_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
    ]
  }
}

data "aws_iam_policy_document" "s3_vault_data_replication_policy" {
  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetReplicationConfiguration",
    ]

    resources = [
      local.s3_bucket_arn,
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObjectVersion",
      "s3:GetObjectVersionAcl",
    ]

    resources = [
      "${local.s3_bucket_arn}/*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:ReplicateObject",
      "s3:ReplicateDelete",
    ]

    resources = [
      "${aws_s3_bucket.vault_data_dr.arn}/*",
    ]
  }
}

resource "aws_iam_role" "s3_vault_data_replication_role" {
  name                  = "s3-data-replication-${local.resource_id}"
  description           = "Role to allow cross region replication from the vault data s3 bucket"
  assume_role_policy    = data.aws_iam_policy_document.s3_trust_policy.json
  force_detach_policies = true
}

resource "aws_iam_role_policy" "s3_vault_data_replication_policy" {
  name   = "s3-data-replication-${local.resource_id}"
  role   = aws_iam_role.s3_vault_data_replication_role.id
  policy = data.aws_iam_policy_document.s3_vault_data_replication_policy.json
}

resource "aws_s3_bucket_replication_configuration" "vault_data" {
  bucket = local.s3_bucket_id

  role = aws_iam_role.s3_vault_data_replication_role.arn

  rule {
    id     = "replicate-vault-data"
    status = "Enabled"
    prefix = ""

    destination {
      bucket        = aws_s3_bucket.vault_data_dr.arn
      storage_class = "STANDARD"
    }
  }
}

resource "aws_s3_bucket" "vault_data_dr" {
  provider = aws.dr

  bucket        = "${local.s3_bucket_id}-dr"
  force_destroy = true

  tags = merge(local.tags, {
    Name = "${local.s3_bucket_id}-dr"
  })
}

resource "aws_s3_bucket_versioning" "vault_data_dr" {
  provider = aws.dr

  bucket = aws_s3_bucket.vault_data_dr.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "vault_data_dr" {
  provider = aws.dr

  bucket = aws_s3_bucket.vault_data_dr.bucket

  rule {
    id     = "vault-data-s3-lifecycle-rule"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}