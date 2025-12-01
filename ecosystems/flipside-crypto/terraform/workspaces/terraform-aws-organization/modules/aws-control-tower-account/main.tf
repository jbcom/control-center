locals {
  units = var.context["units"]

  sso = {
    first_name = coalesce(var.sso.first_name, title(split("-", var.name)[0]))
    last_name = coalesce(var.sso.last_name, strcontains(var.name, "-") ? join(" ", [
      for part in slice(split("-", var.name), 1, length(split("-", var.name))) : title(part)
    ]) : "Account")
    email = coalesce(var.sso.email, format("%s@flipsidecrypto.com", lower(var.name)))
  }
}

resource "controltower_aws_account" "this" {
  name                = var.name
  email               = local.sso.email
  organizational_unit = local.units[var.organizational_unit]["control_tower_organizational_unit"]

  organizational_unit_id_on_delete = local.units[var.organizational_unit_on_delete]["id"]
  close_account_on_delete          = var.close_account_on_delete

  sso {
    first_name = local.sso.first_name
    last_name  = local.sso.last_name
    email      = local.sso.email
  }

  tags = merge(var.context["tags"], var.tags)
}

module "account_labels" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//modules/aws/aws-label-aws-account"

  aws_account            = controltower_aws_account.this
  aws_organization_units = local.units
  domains                = var.context["domains"]
  caller_account_id      = var.caller_account_id

  log_file_name = "aws_account_${var.name}.log"
}
