/**
 * AWS Billing Utilities
 *
 * Comprehensive billing management solution that:
 * 1. Deploys billing policy migration utilities via CloudFormation StackSets
 * 2. Migrates legacy aws-portal:* permissions to the new fine-grained IAM model
 * 3. Creates per-account CUR buckets with replication to a central bucket
 * 4. Supports CUR analysis with proper organization structure
 */

# ---------------------------------------------------------------------------------------
# Central CUR Bucket in Management Account
# ---------------------------------------------------------------------------------------
module "central_cur_bucket" {
  source  = "cloudposse/s3-bucket/aws"
  version = "3.1.0"

  name               = "central-cur-${local.account_id}" # Using account_id from config.tf.json
  acl                = "private"
  force_destroy      = false
  enabled            = true
  user_enabled       = false
  versioning_enabled = true

  # Lifecycle rules for cost optimization
  lifecycle_configuration_rules = [
    {
      id      = "archive-old-reports"
      enabled = true

      # Required attributes
      abort_incomplete_multipart_upload_days = 7
      filter_and                             = null
      noncurrent_version_expiration          = { days = 365 }
      noncurrent_version_transition          = []

      # Original config
      filter = {
        prefix = ""
      }
      transition = [
        {
          days          = 90
          storage_class = "STANDARD_IA"
        },
        {
          days          = 365
          storage_class = "GLACIER"
        }
      ]
      expiration = {
        days = 1825 # 5 years
      }
    }
  ]

  # Enable default encryption
  sse_algorithm = "AES256"

  # Tags
  tags = merge(local.context.tags, { # Using context.tags from config.tf.json
    Name    = "Central CUR Bucket"
    Purpose = "Organization Cost and Usage Reports"
  })
}

# Bucket policy to allow member accounts to replicate CUR data
resource "aws_s3_bucket_policy" "central_cur" {
  bucket = module.central_cur_bucket.bucket_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowReplicationFromMemberAccounts"
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags",
          "s3:GetObjectVersionTagging",
          "s3:GetObjectVersion",
          "s3:GetObjectVersionAcl"
        ]
        Resource = "${module.central_cur_bucket.bucket_arn}/organization/${aws_organizations_organization.this.id}/*"
        Condition = {
          StringEquals = {
            "aws:PrincipalOrgID" = aws_organizations_organization.this.id
          }
        }
      },
      {
        Sid       = "DenyUnencryptedObjectUploads"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${module.central_cur_bucket.bucket_arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      },
      {
        Sid       = "DenyInsecureConnections"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = "${module.central_cur_bucket.bucket_arn}/*"
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# ---------------------------------------------------------------------------------------
# Billing Utilities StackSet for Resource OUs (Service-Managed)
# ---------------------------------------------------------------------------------------
resource "aws_cloudformation_stack_set" "billing_utilities" {
  name             = "BillingUtilitiesStackSet"
  description      = "Comprehensive billing management tools for cost data and IAM permissions"
  permission_model = "SERVICE_MANAGED"

  auto_deployment {
    enabled                          = true # Enable auto-deployment for OUs so new accounts get the stack
    retain_stacks_on_account_removal = false
  }

  # Use CloudFormation template directly from file
  template_body = file("${path.module}/templates/billing_utilities.yaml")

  parameters = {
    ManagementAccountId     = local.account_id # Using account_id from config.tf.json
    OrganizationId          = aws_organizations_organization.this.id
    MigrationRoleName       = "BillingUtilitiesRole"
    LambdaFunctionName      = "BillingUtilitiesFunction"
    ScheduleExpression      = "rate(7 days)"
    EnableAutoUpdates       = "true"
    IncludeBillingConductor = "true"
    IncludeCUR              = "true"
    CURBucketPrefix         = "fsc-cur"
    CentralCURBucket        = module.central_cur_bucket.bucket_id
    LambdaCode              = file("${path.module}/lambdas/billing_utilities.py")
  }

  capabilities = ["CAPABILITY_NAMED_IAM"]

  # Ensure the central bucket exists before deploying this stack
  depends_on = [
    module.central_cur_bucket
  ]
}

# ---------------------------------------------------------------------------------------
# Deploy StackSet to Resource OUs (Deployments, Infrastructure, Isolated)
# ---------------------------------------------------------------------------------------
resource "aws_cloudformation_stack_set_instance" "resource_ou_deployment" {
  for_each = local.resource_ous

  stack_set_name = aws_cloudformation_stack_set.billing_utilities.name

  deployment_targets {
    organizational_unit_ids = [each.value.id]
  }

  region = local.region # Changed 'regions' to 'region'

  operation_preferences {
    max_concurrent_count    = 5
    failure_tolerance_count = 1
  }
}

# ---------------------------------------------------------------------------------------
# Deploy StackSet to Testbed Accounts (Self-Managed)
# ---------------------------------------------------------------------------------------
resource "aws_cloudformation_stack_set" "testbed_billing_utilities" {
  name        = "TestbedBillingUtilitiesStackSet"
  description = "Billing utilities for testbed accounts"

  # This is for specific accounts, not service-managed
  permission_model = "SELF_MANAGED"

  # Grant permission to CloudFormation service to assume the administration role
  administration_role_arn = "arn:aws:iam::${local.account_id}:role/AWSCloudFormationStackSetAdministrationRole" # Using account_id from config.tf.json

  # Use the same template and parameters
  template_body = file("${path.module}/templates/billing_utilities.yaml")

  parameters = {
    ManagementAccountId     = local.account_id # Using account_id from config.tf.json
    OrganizationId          = aws_organizations_organization.this.id
    MigrationRoleName       = "BillingUtilitiesRole"
    LambdaFunctionName      = "BillingUtilitiesFunction"
    ScheduleExpression      = "rate(7 days)"
    EnableAutoUpdates       = "true"
    IncludeBillingConductor = "true"
    IncludeCUR              = "true"
    CURBucketPrefix         = "fsc-cur"
    CentralCURBucket        = module.central_cur_bucket.bucket_id
    LambdaCode              = file("${path.module}/lambdas/billing_utilities.py")
  }

  capabilities = ["CAPABILITY_NAMED_IAM"]

  depends_on = [
    module.central_cur_bucket
  ]
}

# Create stack instances for each testbed account
resource "aws_cloudformation_stack_set_instance" "testbed_account_deployment" {
  for_each = local.testbed_account_cfn_roles

  stack_set_name = aws_cloudformation_stack_set.testbed_billing_utilities.name

  account_id = local.testbed_accounts[each.key].id
  region     = local.region

  # AWSControlTowerExecution role is used automatically - no need to specify

  # Deployment preferences
  operation_preferences {
    max_concurrent_count    = 2
    failure_tolerance_count = 0
  }
}

# ---------------------------------------------------------------------------------------
# Budget for the entire organization
# ---------------------------------------------------------------------------------------
resource "aws_budgets_budget" "organization" {
  name         = "OrganizationBudget"
  budget_type  = "COST"
  limit_amount = "10000" # Set a reasonable default budget limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 80 # Set a reasonable threshold percentage
    threshold_type      = "PERCENTAGE"
    notification_type   = "ACTUAL"

    subscriber_email_addresses = ["admin@example.com"] # Replace with your actual admin email
  }

  # Add forecasted notification
  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 100
    threshold_type      = "PERCENTAGE"
    notification_type   = "FORECASTED"

    subscriber_email_addresses = ["admin@example.com"] # Replace with your actual admin email
  }
}

# ---------------------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------------------
output "billing_enabled" {
  value       = true
  description = "Whether AWS Billing integration is enabled"
}

output "cur_bucket_name" {
  value       = module.central_cur_bucket.bucket_id
  description = "Name of the S3 bucket storing Cost and Usage Reports"
}

locals {
  # CUDOS specific configuration
  cudos_config = {
    report_time_unit          = "DAILY"
    lookback_period_in_months = 38 # Analyze past 38 months as mentioned
    cur_report_s3_prefix      = "cur-data"
    cur_report_s3_region      = local.region # Using the region from config.tf.json

    # Additional options
    athena_query_results_s3_prefix = "athena-results"
    quicksight_namespace           = "default"
    create_cur_report              = true

    # Bucket names for CUDOS
    cloudformation_bucket_name = "fsc-cudos-cloudformation-${local.account_id}"
    dashboards_bucket_name     = "fsc-cudos-dashboards-${local.account_id}"
  }
}

# Create the destination S3 bucket first
resource "aws_s3_bucket" "cudos_destination" {
  bucket = "cudos-destination-${local.account_id}"

  tags = merge(local.context.tags, {
    Component = "BillingDestination"
  })
}

# CUDOS Destination module - Creates dashboards and analysis tools
module "cudos_destination" {
  source  = "appvia/cudos/aws//modules/destination"
  version = "3.0.0" # Updated to latest available version

  providers = {
    aws           = aws
    aws.us_east_1 = aws
  }

  # Required parameters
  cloudformation_bucket_name = local.cudos_config.cloudformation_bucket_name
  dashboards_bucket_name     = local.cudos_config.dashboards_bucket_name

  # QuickSight configuration
  quicksight_admin_email     = "admin@example.com" # Replace with your actual admin email
  quicksight_admin_username  = "admin"
  quicksight_dashboard_owner = "admin"

  # Security configuration
  enable_sso = false # Set to true if you have SAML metadata

  # Additional configuration  
  payer_accounts = [local.account_id]

  tags = merge(local.context.tags, { # Using context.tags from config.tf.json
    Component = "BillingDestination"
  })
}

# CUDOS Source module - Creates and configures the CUR setup
module "cudos_source" {
  source  = "appvia/cudos/aws//modules/source"
  version = "3.0.0" # Updated to latest available version

  providers = {
    aws           = aws
    aws.us_east_1 = aws
  }

  # Required parameters
  destination_account_id = local.account_id # Same account as source
  destination_bucket_arn = aws_s3_bucket.cudos_destination.arn
  stacks_bucket_name     = local.cudos_config.cloudformation_bucket_name

  # Optional parameters
  enable_backup_module          = false
  enable_budgets_module         = true
  enable_ecs_chargeback_module  = false
  enable_health_events_module   = false
  enable_inventory_module       = true
  enable_rds_utilization_module = false
  enable_scad                   = true

  tags = merge(local.context.tags, { # Using context.tags from config.tf.json
    Component = "BillingSource"
  })

  depends_on = [module.cudos_destination]
}

# CloudWatch Dashboard with key metrics - supplementary to CUDOS dashboards
resource "aws_cloudwatch_dashboard" "billing_summary" {
  dashboard_name = "BillingSummary"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 1
        properties = {
          markdown = "# AWS Organization Billing Summary\nDetailed analysis available in [CUDOS dashboards](https://${local.region}.console.aws.amazon.com/quicksight/)" # Using region from config.tf.json
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 12
        height = 6
        properties = {
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"],
          ]
          region = local.region # Using region from config.tf.json
          title  = "Current Month Cost"
          period = 86400
          stat   = "Maximum"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 1
        width  = 12
        height = 6
        properties = {
          view = "pie"
          metrics = [
            for linked_account_id in slice(distinct([
              for account_id, account in local.accounts : account_id
            ]), 0, 10) : ["AWS/Billing", "EstimatedCharges", "LinkedAccount", linked_account_id, "Currency", "USD"]
          ]
          region = local.region # Using region from config.tf.json
          title  = "Top 10 Accounts"
          period = 86400
          stat   = "Maximum"
        }
      }
    ]
  })
}

# Add outputs for the CUDOS resources
output "cudos_bucket_name" {
  value       = aws_s3_bucket.cudos_destination.arn
  description = "ARN of the S3 bucket storing Cost and Usage Reports (CUDOS)"
}

output "cudos_glue_database_name" {
  value       = "cid_cur_crawler" # Default name used by CUDOS
  description = "Name of the Glue database for CUR data (CUDOS)"
}

output "cudos_athena_workgroup_name" {
  value       = "cid-primary" # Default workgroup used by CUDOS
  description = "Name of the Athena workgroup for CUR analysis (CUDOS)"
}

output "quicksight_dashboard_url" {
  value       = "https://${local.region}.quicksight.aws.amazon.com/sn/dashboards/cid-dashboards" # Using region from config.tf.json
  description = "URL to the CUDOS QuickSight dashboard"
}

# Export billing configuration for record generation
output "billing" {
  description = "Billing configuration details"
  value = {
    enabled = local.billing_enabled
    cudos = {
      enabled          = local.cudos_enabled
      dashboard_url    = local.quicksight_dashboard_url
      bucket_name      = try(module.cudos_destination.module.collector.aws_s3_bucket.this.id, null)
      athena_workgroup = local.cudos_athena_workgroup_name
      glue_database    = local.cudos_glue_database_name
    }
    cur = {
      bucket_name = try(module.central_cur_bucket.bucket_name, null)
      report_name = try(aws_cur_report_definition.organization.report_name, null)
    }
  }
}

# AWS Billing Main
# This file serves as the entry point for the billing workspace

# Collect outputs for permanent record
locals {
  records_config = {
    billing = {
      enabled = local.billing_enabled
      cudos = {
        enabled          = local.cudos_enabled
        dashboard_url    = local.quicksight_dashboard_url
        bucket_name      = try(module.cudos_destination.module.collector.aws_s3_bucket.this.id, null)
        athena_workgroup = local.cudos_athena_workgroup_name
        glue_database    = local.cudos_glue_database_name
      }
      cur = {
        bucket_name = try(module.central_cur_bucket.bucket_name, null)
        report_name = try(aws_cur_report_definition.organization.report_name, null)
      }
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
} 