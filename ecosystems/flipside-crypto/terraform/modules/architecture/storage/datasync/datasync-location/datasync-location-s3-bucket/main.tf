locals {
  enabled = var.config["datasync"]
  name    = "datasync-location-s3-${var.data["bucket_id"]}"
  arn     = var.data["bucket_arn"]

  tags = merge(var.context["tags"], {
    Name = local.name
  })
}

data "aws_iam_policy_document" "bucket_access" {
  statement {
    actions = [
      "s3:*",
    ]

    resources = [
      local.arn,
      "${local.arn}:/*",
      "${local.arn}:job/*"
    ]
  }
}

resource "aws_iam_policy" "bucket_access" {
  count = local.enabled ? 1 : 0

  name = local.name

  policy = data.aws_iam_policy_document.bucket_access.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "bucket_access" {
  count = local.enabled ? 1 : 0

  policy_arn = join("", aws_iam_policy.bucket_access.*.arn)
  role       = var.role_name
}

resource "aws_datasync_location_s3" "default" {
  count = local.enabled ? 1 : 0

  s3_bucket_arn    = local.arn
  s3_storage_class = var.config["datasync_storage_class"]

  subdirectory = var.config["datasync_subdirectory"]

  s3_config {
    bucket_access_role_arn = var.role_arn
  }

  tags = local.tags
}