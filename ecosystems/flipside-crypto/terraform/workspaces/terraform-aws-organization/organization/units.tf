# Create organizational units using metadata from metadata.tf
resource "aws_organizations_organizational_unit" "units" {
  for_each = local.context.units

  name      = each.value.name
  parent_id = local.organization_root_id

  tags = merge(local.tags, {
    Name            = each.value.name
    Classifications = join(" ", each.value.classifications)
    Environment     = each.value.environment
  })
}

locals {
  units_data = {
    for unit, data in aws_organizations_organizational_unit.units : unit => merge(local.context.units[unit], data, {
      control_tower_organizational_unit = "${data.name} (${data.id})"
    })
  }

  suspended_ou_id = aws_organizations_organizational_unit.units["suspended"].id

  reconciled_units_accounts_data = {
    for account_name, account_data in local.context.accounts : account_name => try(merge(account_data, {
      for k, v in local.units_data[account_data.organizational_unit] : "ou_${k}" => v
      if k != "control_tower_organizational_unit"
      }, {
      control_tower_organizational_unit = local.units_data[account_data.organizational_unit].control_tower_organizational_unit
      }), merge(account_data, {
      ou_id                             = local.organization_root_id
      control_tower_organizational_unit = null
    }))
  }

  # No longer needed as we can access landing_zone_name directly from units_data
}
