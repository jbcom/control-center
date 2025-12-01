# AWS SecurityHub Main
# This file manages SecurityHub configuration across the organization

# Get the AWS Organizations resource
data "aws_organizations_organization" "this" {}

# SecurityHub organization admin account
resource "aws_securityhub_organization_admin_account" "this" {
  admin_account_id = "383686502118"

  depends_on = [data.aws_organizations_organization.this]
}

# Import statements for existing SecurityHub resources
# These will be used when importing existing resources
# import {
#   to = aws_securityhub_organization_admin_account.this
#   id = "383686502118"
# }

locals {
  # Collect outputs for permanent record
  records_config = {
    securityhub = {
      admin_account = try(aws_securityhub_organization_admin_account.this.admin_account_id, null)
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}

# Export SecurityHub configuration for record generation
output "securityhub" {
  description = "SecurityHub configuration"
  value = {
    admin_account = try(aws_securityhub_organization_admin_account.this.admin_account_id, null)
  }
}
