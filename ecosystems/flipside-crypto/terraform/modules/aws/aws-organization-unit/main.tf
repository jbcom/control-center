locals {
  unit_name = title(coalesce(var.unit_config.unit_name, var.unit_name))

  tags = merge(var.tags, {
    Name = local.unit_name
  })
}

resource "aws_organizations_organizational_unit" "this" {
  name      = local.unit_name
  parent_id = var.parent_id

  tags = local.tags
}

locals {
  unit_data = {
    organizational_unit = local.unit_name

    child_accounts = {
      for ou_data in aws_organizations_organizational_unit.this.accounts : ou_data["name"] => ou_data
    }

    ou_arn       = aws_organizations_organizational_unit.this.arn
    ou_id        = aws_organizations_organizational_unit.this.id
    ou_name      = aws_organizations_organizational_unit.this.name
    ou_parent_id = aws_organizations_organizational_unit.this.parent_id
    ou_tags      = aws_organizations_organizational_unit.this.tags

    spoke = var.unit_config.spoke
  }
}