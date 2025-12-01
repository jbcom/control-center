# AWS Organizations Units Main
# This file serves as the entry point for the units workspace

# Direct Organizational Unit resources
resource "aws_organizations_organizational_unit" "units" {
  for_each = local.context.units

  name      = each.value.name
  parent_id = local.context.root_id

  tags = merge(try(local.context.tags, {}), {
    Name            = each.value.name
    Classifications = join(" ", each.value.classifications)
    Type            = try(each.value.classification_type, "")
    Environment     = try(each.value.environment, "global")
  })
}

# Moved statements to handle the transition from module resources to direct resources
moved {
  from = module.organization_units["deployments"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["deployments"]
}

moved {
  from = module.organization_units["infrastructure"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["infrastructure"]
}

moved {
  from = module.organization_units["isolated"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["isolated"]
}

moved {
  from = module.organization_units["sandbox"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["sandbox"]
}

moved {
  from = module.organization_units["security"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["security"]
}

moved {
  from = module.organization_units["suspended"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["suspended"]
}

moved {
  from = module.organization_units["aft"].aws_organizations_organizational_unit.this
  to   = aws_organizations_organizational_unit.units["aft"]
}

locals {
  records_config = {
    units = {
      for unit_name, unit_data in aws_organizations_organizational_unit.units : unit_name => merge(unit_data, {
        control_tower_organizational_unit = "${unit_data.name} (${unit_data.id})"
      })
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}
