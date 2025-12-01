# CloudTrail S3 bucket
resource "aws_s3_bucket" "cloudtrail" {
  bucket        = "organization-cloudtrail-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# CloudTrail Organization Configuration
resource "aws_cloudtrail" "organization" {
  name                          = "organization-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  is_organization_trail         = true
  is_multi_region_trail         = try(local.context.organization.services.cloudtrail.settings.is_multi_region_trail, true)
  include_global_service_events = try(local.context.organization.services.cloudtrail.settings.include_global_service_events, true)
  enable_log_file_validation    = try(local.context.organization.services.cloudtrail.settings.enable_log_file_validation, true)
  enable_logging                = true

  insight_selector {
    insight_type = "ApiCallRateInsight"
  }

  depends_on = [
    aws_organizations_organization.this,
    aws_s3_bucket_policy.cloudtrail
  ]
} 