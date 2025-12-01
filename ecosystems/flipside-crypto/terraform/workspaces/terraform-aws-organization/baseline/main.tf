# AWS Baseline Main
# This file manages baseline security and compliance resources

locals {
  # Get security services from delegation workspace
  security_services = try(local.context.delegation.security_services, {})

  # Get logging configuration from context
  log_configs = try(local.context.organization.logging, {})

  # Extract account info
  accounts = try(local.context.organization.all_accounts, {})
}

# Create organization-wide CloudTrail
resource "aws_cloudtrail" "organization" {
  name                          = try(local.log_configs.log_archive.cloudtrail.main_bucket.name, "aws-controltower-BaselineCloudTrail")
  s3_bucket_name                = try(local.log_configs.log_archive.cloudtrail.main_bucket.name, "aws-controltower-logs-850178735765-us-east-1")
  s3_key_prefix                 = try(local.log_configs.log_archive.cloudtrail.main_bucket.prefix, "o-fdri2qhe6u")
  include_global_service_events = true
  enable_log_file_validation    = true
  is_multi_region_trail         = true
  is_organization_trail         = true
}

# Export baseline configuration for record generation
output "baseline" {
  description = "Baseline security configurations"
  value = {
    cloudtrail = {
      name                          = aws_cloudtrail.organization.name
      s3_bucket                     = aws_cloudtrail.organization.s3_bucket_name
      include_global_service_events = aws_cloudtrail.organization.include_global_service_events
      is_organization_trail         = aws_cloudtrail.organization.is_organization_trail
    }

    security_services = local.security_services
  }
} 