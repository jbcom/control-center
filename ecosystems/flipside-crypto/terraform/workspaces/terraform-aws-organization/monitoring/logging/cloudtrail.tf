# CloudTrail S3 Bucket Configuration
# This bucket is used to store CloudTrail logs from all accounts in the organization

locals {
  org_id = local.context.organization.id

  # Generate bucket name for CloudTrail logs
  cloudtrail_bucket_name = "fsc-cloudtrail-logs-${local.org_id}"

  # Extract account details for reference
  accounts = local.context.networked_accounts_by_json_key

  # Generate dynamic lifecycle rules for both management and data events for each account
  account_lifecycle_rules = flatten([
    # Default rule for all objects - just set retention
    {
      enabled = true
      id      = "default-retention"

      abort_incomplete_multipart_upload_days = 7

      filter = {
        prefix = ""
      }

      # Standard retention
      expiration = {
        days = 365
      }
    },

    # Generate account-specific rules for data events only
    flatten([
      for json_key, account_data in local.accounts : [
        # Data events lifecycle rule - higher volume events need special handling
        {
          enabled = true
          id      = "${json_key}-data-lifecycle"

          abort_incomplete_multipart_upload_days = 7

          # Apply rule to data events prefix for this account
          filter = {
            prefix = "${json_key}/data/"
          }

          # Aggressive archival for data events with required timing gaps
          transition = [
            {
              days          = 1 # Move to GLACIER_IR immediately after first day
              storage_class = "GLACIER_IR"
            },
            {
              days          = 91 # Required 90-day gap after GLACIER_IR
              storage_class = "GLACIER"
            },
            {
              days          = 181 # Required 90-day gap after GLACIER
              storage_class = "DEEP_ARCHIVE"
            }
          ]

          # Retention must be at least 90 days after final transition
          expiration = {
            days = 271 # 90 days after DEEP_ARCHIVE transition at 181 days
          }
        }
      ]
    ])
  ])
}

data "aws_iam_policy_document" "cloudtrail_bucket_policy" {
  # Allow CloudTrail service to check bucket ACL
  statement {
    sid = "AWSCloudTrailAclCheck"

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions = [
      "s3:GetBucketAcl",
    ]

    resources = [
      "arn:aws:s3:::${local.cloudtrail_bucket_name}",
    ]

    # Restrict to CloudTrail from specific accounts
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = local.source_account_ids
    }
  }

  # Allow CloudTrail service to write logs to the bucket
  statement {
    sid = "AWSCloudTrailWrite"

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions = [
      "s3:PutObject",
    ]

    # Resources need to be structured for each account's path pattern
    resources = flatten([
      for account_id in local.source_account_ids : [
        # Both prefixed and account-based path patterns
        "arn:aws:s3:::${local.cloudtrail_bucket_name}/*/management/AWSLogs/${account_id}/*",
        "arn:aws:s3:::${local.cloudtrail_bucket_name}/*/data/AWSLogs/${account_id}/*",
        # Legacy/default path pattern
        "arn:aws:s3:::${local.cloudtrail_bucket_name}/AWSLogs/${account_id}/*"
      ]
    ])

    # Two important conditions for CloudTrail
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = local.source_account_ids
    }
  }

  # Allow AWS Config if needed
  statement {
    sid = "AWSConfigBucketPermissions"

    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }

    actions = [
      "s3:PutObject",
    ]

    resources = flatten([
      for account_id in local.source_account_ids : [
        "arn:aws:s3:::${local.cloudtrail_bucket_name}/AWSLogs/${account_id}/Config/*"
      ]
    ])

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = local.source_account_ids
    }
  }

  # Allow SSO roles, Lambda functions, admin bot users, and Grafana, to access the bucket
  statement {
    sid = "AllowRoleAccess"

    principals {
      type = "AWS"
      identifiers = concat(
        # SSO Roles
        values(module.aws_sso_roles.roles),
        local.context.admin_bot_users,
        [
          local.context.bots.grafana_cloudwatch.user_arn,
        ],
        flatten([
          for account in values(local.architecture) : account.cloudtrail_authorized_principals
        ])
      )
    }

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]

    resources = [
      "arn:aws:s3:::${local.cloudtrail_bucket_name}",
      "arn:aws:s3:::${local.cloudtrail_bucket_name}/*"
    ]
  }
}

module "aws_sso_roles" {
  source = "../../../../modules/aws/aws-sso-roles-data"
}

# S3 bucket for CloudTrail logs using CloudPosse module
module "cloudtrail_bucket" {
  source  = "cloudposse/s3-bucket/aws"
  version = "4.10.0"

  bucket_name = local.cloudtrail_bucket_name
  name        = local.cloudtrail_bucket_name

  # Set bucket properties - FIXED: Changed from BucketOwnerEnforced to BucketOwnerPreferred
  # This is necessary for CloudTrail to set ACLs on objects
  acl                     = "log-delivery-write"
  force_destroy           = true
  versioning_enabled      = false
  sse_algorithm           = "AES256"
  allow_ssl_requests_only = true
  s3_object_ownership     = "BucketOwnerPreferred" # Changed from BucketOwnerEnforced

  # Block public access
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Define extended permissions for the S3 user to access CloudWatch
  allowed_bucket_actions = [
    "s3:PutObject",
    "s3:PutObjectAcl",
    "s3:GetObject",
    "s3:DeleteObject",
    "s3:ListBucket",
    "s3:ListBucketMultipartUploads",
    "s3:GetBucketLocation",
    "s3:AbortMultipartUpload",
  ]

  # Use our dynamic account-specific lifecycle rules
  lifecycle_configuration_rules = local.account_lifecycle_rules

  # Use source policy document
  source_policy_documents = [
    data.aws_iam_policy_document.cloudtrail_bucket_policy.json,
  ]

  # Set context for naming and tagging
  context = local.context
}

locals {
  cloudtrail_bucket_id  = module.cloudtrail_bucket.bucket_id
  cloudtrail_bucket_arn = module.cloudtrail_bucket.bucket_arn

  enabled_lambdas = {
    for module_name, module_architecture in local.architecture : module_name =>
    module_architecture.lambda_function_qualified_arn
    if try(coalesce(module_architecture.lambda_function_qualified_arn), null) != null
  }
}

# Create S3 bucket notification configuration for Lambda functions
resource "aws_s3_bucket_notification" "cloudtrail_bucket_notification" {
  bucket = module.cloudtrail_bucket.bucket_id

  # Dynamically create Lambda function notifications for each source account
  dynamic "lambda_function" {
    for_each = local.enabled_lambdas

    content {
      lambda_function_arn = lambda_function.value
      events              = ["s3:ObjectCreated:*"]

      filter_prefix = "AWSLogs/${lambda_function.key}/"
      filter_suffix = ".json.gz"
    }
  }
}

# Add Intelligent-Tiering configurations
# Default configuration for entire bucket
resource "aws_s3_bucket_intelligent_tiering_configuration" "cloudtrail_bucket" {
  bucket = module.cloudtrail_bucket.bucket_id
  name   = "EntireBucket"

  # Archive tiers for all objects except those handled by lifecycle rules
  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }
  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

# Disable Intelligent-Tiering for data events
resource "aws_s3_bucket_intelligent_tiering_configuration" "cloudtrail_data" {
  bucket = module.cloudtrail_bucket.bucket_id
  name   = "DataEvents"
  status = "Disabled"

  filter {
    prefix = "*/data/"
  }

  # Required even when disabled
  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}
