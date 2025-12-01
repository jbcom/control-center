module "organization_metadata" {
  source = "git@github.com:FlipsideCrypto/terraform-organization.git//modules/organization-metadata"
}

locals {
  organization_data              = module.organization_metadata.metadata
  networked_accounts_by_json_key = local.organization_data["networked_accounts_by_json_key"]
}

resource "aws_ram_resource_share" "default" {
  for_each = {
    for json_key, account_data in local.networked_accounts_by_json_key : json_key => account_data if account_data["id"] != data.aws_caller_identity.current.account_id
  }

  name                      = each.key
  allow_external_principals = false

  tags = lookup(each.value, "tags", var.context["tags"])
}

resource "aws_ram_principal_association" "default" {
  for_each = aws_ram_resource_share.default

  principal          = local.networked_accounts_by_json_key[each.key]["id"]
  resource_share_arn = each.value.arn
}

locals {
  records_config = {
    ram_associations = {
      for json_key, share_data in aws_ram_resource_share.default : json_key => share_data["arn"]
    }
  }
}

module "permanent_record" {
  source = "../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}