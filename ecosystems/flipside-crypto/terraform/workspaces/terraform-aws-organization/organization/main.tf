locals {
  tags              = local.context.tags
  domains           = local.context.domains
  live_environments = local.context.live_environments
}

locals {
  records_config = merge(aws_organizations_organization.this, local.classified_accounts, {
    accounts = local.aws_accounts

    accounts_by_name = {
      for account in values(local.aws_accounts) : account.account_name => account
    }

    accounts_by_json_key = {
      for account in values(local.aws_accounts) : account.json_key => account
    }

    units = local.units_data
    kms   = module.kms
  })
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspace_dir}"

  log_file_name = "permanent_record.log"
}
