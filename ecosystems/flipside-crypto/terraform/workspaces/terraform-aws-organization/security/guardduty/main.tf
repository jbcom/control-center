# AWS GuardDuty Main
# This file manages GuardDuty configuration across the organization

# Get the AWS Organizations resource
data "aws_organizations_organization" "this" {}

# GuardDuty detector in the management account
resource "aws_guardduty_detector" "this" {
  enable                       = true
  finding_publishing_frequency = "SIX_HOURS"
}

# GuardDuty organization admin account
resource "aws_guardduty_organization_admin_account" "this" {
  admin_account_id = "383686502118"

  depends_on = [data.aws_organizations_organization.this]
}

# Import statements for existing GuardDuty resources
# These will be used when importing existing resources
# import {
#   to = aws_guardduty_detector.this
#   id = "44c29b8072f3b4af0d68f26ccba5e5a4"
# }
# 
# import {
#   to = aws_guardduty_organization_admin_account.this
#   id = "383686502118"
# }

locals {
  # Collect outputs for permanent record
  records_config = {
    guardduty = {
      detector_id   = aws_guardduty_detector.this.id
      admin_account = try(aws_guardduty_organization_admin_account.this.admin_account_id, null)
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}

# Export GuardDuty configuration for record generation
output "guardduty" {
  description = "GuardDuty configuration"
  value = {
    detector_id   = aws_guardduty_detector.this.id
    admin_account = try(aws_guardduty_organization_admin_account.this.admin_account_id, null)
  }
}
