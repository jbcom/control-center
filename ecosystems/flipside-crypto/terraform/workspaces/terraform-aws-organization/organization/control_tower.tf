# AWS Control Tower Configuration
# This file manages Control Tower landing zone and controls

# AWS Control Tower Landing Zone
resource "awscc_controltower_landing_zone" "this" {
  count = local.context.organization.services.controltower.enabled ? 1 : 0

  manifest = jsonencode({
    "governedRegions" : toset(local.context.control_tower.landing_zone.governed_regions),
    "organizationStructure" : local.context.control_tower.organization_structure,
    "centralizedLogging" : {
      "accountId" : aws_organizations_account.organization_accounts["log_archive"].id,
      "configurations" : {
        "loggingBucket" : {
          "retentionDays" : tostring(local.context.control_tower.landing_zone.centralized_logging.configurations.logging_bucket.retention_days)
        },
        "accessLoggingBucket" : {
          "retentionDays" : tostring(local.context.control_tower.landing_zone.centralized_logging.configurations.access_logging_bucket.retention_days)
        },
        "kmsKeyArn" : local.kms_key_arn
      },
      "enabled" : local.context.control_tower.landing_zone.centralized_logging.enabled
    },
    "securityRoles" : {
      "accountId" : aws_organizations_account.organization_accounts["audit"].id
    },
    "accessManagement" : {
      "enabled" : local.context.control_tower.landing_zone.access_management.enabled
    }
  })
  version = local.context.control_tower.landing_zone.version
}

# Process Control Tower controls
locals {
  # Get the organization ID from the AWS Organizations data source
  organization_id = aws_organizations_organization.this.id

  # Process standard controls
  processed_controls = {
    for key, control in local.context.control_tower.processed_controls : key => {
      control_name = control.control_name
      target_ou    = control.target_ou
      ou_id        = aws_organizations_organizational_unit.units[control.target_ou].id
    }
  }

  # Process controls with parameters
  processed_controls_with_params = {
    for key, control in local.context.control_tower.processed_controls_with_params : key => {
      control_name = control.control_name
      target_ou    = control.target_ou
      ou_id        = aws_organizations_organizational_unit.units[control.target_ou].id
      parameters   = try(control.parameters, {})
    }
  }

  # Control Tower configuration for records
  control_tower_config = {
    landing_zone_id              = try(awscc_controltower_landing_zone.this[0].landing_zone_identifier, null)
    enabled_controls             = local.processed_controls
    enabled_controls_with_params = local.processed_controls_with_params
  }
}
