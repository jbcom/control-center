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