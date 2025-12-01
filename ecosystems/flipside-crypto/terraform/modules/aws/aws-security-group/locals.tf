locals {
  tags = merge(var.tags, {
    Name = var.security_group_name
  })

  inline = var.inline_rules_enabled

  allow_all_egress = var.enabled && var.allow_all_egress

  default_rule_description = "Managed by Terraform"

  create_security_group = var.enabled && length(var.target_security_group_id) == 0


  security_group_id = var.enabled ? (
    # Use coalesce() here to hack an error message into the output
    local.create_security_group ? join("", aws_security_group.this.*.id) : coalesce(var.target_security_group_id[0],
    "var.target_security_group_id contains null value. Omit value if you want this module to create a security group.")
  ) : null
}