resource "controltower_aws_account" "this" {
  name                = var.account.name
  email               = try(var.account.sso.email, format("%s@flipsidecrypto.com", lower(var.account.name)))
  organizational_unit = var.units[var.account.organizational_unit].control_tower_organizational_unit

  organizational_unit_id_on_delete = var.units[try(var.account.organizational_unit_on_delete, "Suspended")].id
  close_account_on_delete          = try(var.account.close_on_deletion, true)

  sso {
    first_name = try(var.account.sso.first_name, title(split("-", var.account.name)[0]))
    last_name = try(var.account.sso.last_name, strcontains(var.account.name, "-") ? join(" ", [
      for part in slice(split("-", var.account.name), 1, length(split("-", var.account.name))) : title(part)
    ]) : "Account")
    email = try(var.account.sso.email, format("%s@flipsidecrypto.com", lower(var.account.name)))
  }

  # Pass tags directly
  tags = merge(try(var.context.tags, {}), var.tags, try(var.account.tags, {}))
}

module "account_labels" {
  source = "../aws-account-labels"

  # Map IDs properly for Control Tower accounts - merge the resource with overrides
  account = merge(controltower_aws_account.this, {
    provisioned_product_id = controltower_aws_account.this.id
    id                     = controltower_aws_account.this.account_id
  })
  units             = var.units
  domains           = var.context.domains
  caller_account_id = var.caller_account_id
}
