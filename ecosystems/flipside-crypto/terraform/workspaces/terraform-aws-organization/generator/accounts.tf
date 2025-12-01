module "new_aws_controltower_accounts_from_google" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-get-new-aws-controltower-accounts-from-google"

  aws_organization_units = local.units

  default_environment = local.environment

  log_file_name = "new_aws_controltower_accounts_from_google.log"
}

locals {
  user_accounts = module.new_aws_controltower_accounts_from_google.accounts

  system_accounts = {
    for account_name, account_data in merge(local.context.organization.root.accounts, local.unit_accounts) :
    account_name => merge(account_data, {
      environment = try(coalesce(account_data.environment), local.unit_environments[account_data.organizational_unit], local.environment)

      email = coalesce(try(account_data.sso.email,
        account_data.sso_user_email,
        one([
          for email_data in account_data.emails : email_data.address if email_data.primary
        ]),
        account_data.account_email,
        account_data.email,
        ""),
      "${lower(replace(replace(account_data.name, " ", "-"), "_", "-"))}@flipsidecrypto.com")

      first_name = coalesce(
        try(account_data.sso.first_name,
          account_data.first_name,
          account_data.given_name,
        ""),
        length(split("-", account_data.name)) > 1 ? split("-", account_data.name)[0] : account_data.name
      )

      # For last_name, fall back to the second part of the account name or "Account" if no hyphen
      last_name = coalesce(
        try(account_data.sso.last_name,
          account_data.last_name,
          account_data.family_name,
        ""),
        length(split("-", account_data.name)) > 1 ? split("-", account_data.name)[1] : "Account"
      )

      control_tower_managed = lookup(account_data, "control_tower_managed", true)

      classifications = sort(distinct(concat(
        try(compact(account_data.classifications), []),
        try(local.unit_classifications[account_data.organizational_unit], []),
      )))
    })
  }

  accounts = {
    for account_key, account_config in merge(local.user_accounts, local.system_accounts) : account_key => merge(account_config, {
      execution_role_name = contains(keys(account_config), "execution_role_name") ? account_config["execution_role_name"] : "AWSControlTowerExecution"

      classifications = try([
        for classification in account_config.classifications : trim(replace(classification, "/[^a-zA-Z0-9]+/", "_"), "_")
      ], [])
    })
  }
}
