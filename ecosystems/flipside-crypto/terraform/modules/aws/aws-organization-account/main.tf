resource "aws_organizations_account" "this" {
  name      = var.account.name
  email     = try(var.account.email, "${lower(var.account.name)}@flipsidecrypto.com")
  role_name = try(var.account.role_name, "OrganizationAccountAccessRole")

  iam_user_access_to_billing = try(var.account.iam_user_access_to_billing, "ALLOW")
  close_on_deletion          = try(var.account.close_on_deletion, true)
  create_govcloud            = try(var.account.create_govcloud, false)

  parent_id = try(var.account.parent, null) != null ? var.units[var.account.parent].id : null

  # Pass tags directly
  tags = merge(try(var.context.tags, {}), try(var.account.tags, {}))

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
  source = "../aws-account-labels"

  # AWS Organizations account - merge the resource with necessary overrides
  account = merge(aws_organizations_account.this, {
    provisioned_product_id = null # Not a Control Tower account
    account_id             = aws_organizations_account.this.id
  })
  units             = var.units
  domains           = var.context.domains
  caller_account_id = var.caller_account_id
}
