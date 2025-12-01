# Create the organizational unit
resource "aws_organizations_organizational_unit" "this" {
  name      = var.name
  parent_id = var.parent_id

  tags = merge(var.tags, {
    Name            = var.name
    Classifications = join(var.classifications_delimiter, var.classifications)
  })
}

# Process unit labels
locals {
  # Basic unit information
  id        = aws_organizations_organizational_unit.this.id
  name      = var.name
  parent_id = var.parent_id
  arn       = aws_organizations_organizational_unit.this.arn

  # Tags
  tags     = aws_organizations_organizational_unit.this.tags
  tags_all = aws_organizations_organizational_unit.this.tags_all

  # Formatted name with ID for Control Tower
  formatted_name = "${var.name} (${aws_organizations_organizational_unit.this.id})"

  # Unit with all properties
  unit = {
    id        = local.id
    name      = local.name
    parent_id = local.parent_id
    arn       = local.arn
    tags      = local.tags
    tags_all  = local.tags_all
    accounts  = []
  }
}
