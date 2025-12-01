output "unit" {
  description = "The organizational unit with all properties"
  value = merge({
    for k, v in aws_organizations_organizational_unit.this : k => v if k != "accounts"
    }, {
    control_tower_organizational_unit = "${aws_organizations_organizational_unit.this.name} (${aws_organizations_organizational_unit.this.id})"
  })
}
