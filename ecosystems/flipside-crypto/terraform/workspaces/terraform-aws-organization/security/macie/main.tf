# AWS Macie Main
# This file manages Macie configuration across the organization

# Get the AWS Organizations resource
data "aws_organizations_organization" "this" {}

# Macie organization admin account
resource "aws_macie2_organization_admin_account" "this" {
  admin_account_id = "383686502118"

  depends_on = [data.aws_organizations_organization.this]
}

# Import statements for existing Macie resources
# These will be used when importing existing resources
# import {
#   to = aws_macie2_organization_admin_account.this
#   id = "383686502118"
# }

locals {
  # Collect outputs for permanent record
  records_config = {
    macie = {
      admin_account = try(aws_macie2_organization_admin_account.this.admin_account_id, null)
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}

# Export Macie configuration for record generation
output "macie" {
  description = "Macie configuration"
  value = {
    admin_account = try(aws_macie2_organization_admin_account.this.admin_account_id, null)
  }
}
