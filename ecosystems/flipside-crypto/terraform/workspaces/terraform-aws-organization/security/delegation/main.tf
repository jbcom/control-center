# AWS Security Delegation Main
# This file manages delegated administrators for security services

# Get the AWS Organizations resource
data "aws_organizations_organization" "this" {}

# Delegated administrator configuration using the preprocessed map from account settings
resource "aws_organizations_delegated_administrator" "this" {
  for_each = {
    for service, config in try(local.context.organization.delegated_administrators, {}) :
    service => config if try(config.account_id, null) != null
  }

  account_id        = each.value.account_id
  service_principal = each.key

  depends_on = [data.aws_organizations_organization.this]
}

# Import statements for existing delegated administrators
# These will be used when importing existing resources
# import {
#   to = aws_organizations_delegated_administrator.this["security:config.amazonaws.com"]
#   id = "383686502118:config.amazonaws.com"
# }
# 
# import {
#   to = aws_organizations_delegated_administrator.this["security:guardduty.amazonaws.com"]
#   id = "383686502118:guardduty.amazonaws.com"
# }
# 
# import {
#   to = aws_organizations_delegated_administrator.this["log_archive:config.amazonaws.com"]
#   id = "850178735765:config.amazonaws.com"
# }
# 
# import {
#   to = aws_organizations_delegated_administrator.this["transit:inspector2.amazonaws.com"]
#   id = "734995239048:inspector2.amazonaws.com"
# }
# 
# import {
#   to = aws_organizations_delegated_administrator.this["transit:ipam.amazonaws.com"]
#   id = "734995239048:ipam.amazonaws.com"
# }
# 
# import {
#   to = aws_organizations_delegated_administrator.this["transit:sso.amazonaws.com"]
#   id = "734995239048:sso.amazonaws.com"
# }

locals {
  # Map of all delegated administrators by service principal
  delegated_admins_by_service = {
    for key, resource in try(aws_organizations_delegated_administrator.this, {}) :
    resource.service_principal => {
      account_id       = resource.account_id
      joined_timestamp = resource.joined_timestamp
    }
  }

  # Collect outputs for permanent record
  records_config = {
    delegated_administrators            = try(aws_organizations_delegated_administrator.this, {})
    delegated_administrators_by_service = local.delegated_admins_by_service
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}

# Export delegated administrators for record generation
output "delegated_administrators" {
  description = "Organization delegated administrators"
  value       = aws_organizations_delegated_administrator.this
}

output "delegated_administrators_by_service" {
  description = "Organization delegated administrators by service"
  value       = local.delegated_admins_by_service
}
