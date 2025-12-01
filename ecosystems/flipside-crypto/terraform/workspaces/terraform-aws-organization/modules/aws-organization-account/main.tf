locals {
  units = var.context["units"]
}

resource "aws_organizations_account" "this" {
  name      = var.name
  email     = coalesce(var.email, "${lower(var.name)}@flipsidecrypto.com")
  role_name = var.role_name

  iam_user_access_to_billing = var.iam_user_access_to_billing
  close_on_deletion          = var.close_on_deletion
  create_govcloud            = var.create_govcloud

  parent_id = var.parent != null ? local.units[var.parent]["id"] : null

  tags = merge(var.context["tags"], var.tags)

  lifecycle {
    ignore_changes = [
      name,
      email,
      iam_user_access_to_billing,
      role_name,
    ]
  }
}

module "account_labels" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//modules/aws/aws-label-aws-account"

  aws_account            = aws_organizations_account.this
  aws_organization_units = local.units
  domains                = var.context["domains"]
  caller_account_id      = var.caller_account_id

  log_file_name = "aws_account_${var.name}.log"
}
