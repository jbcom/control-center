resource "controltower_aws_account" "control_tower_accounts" {
  for_each = {
    for name, account in local.reconciled_units_accounts_data : name => account
    if account.control_tower_managed
  }

  name                             = each.value.name
  email                            = each.value.email
  organizational_unit              = each.value.control_tower_organizational_unit
  organizational_unit_id_on_delete = local.suspended_ou_id

  close_account_on_delete = try(each.value.close_on_delete, true)

  sso {
    first_name = each.value.first_name
    last_name  = each.value.last_name
    email      = try(coalesce(each.value.sso_email), each.value.email)
  }

  tags = merge(local.tags, {
    Name            = each.value.name
    Classifications = join(" ", each.value.classifications)
    Environment     = each.value.environment
  })
}

locals {
  controltower_aws_accounts = {
    for name, account in controltower_aws_account.control_tower_accounts : name =>
    merge(local.reconciled_units_accounts_data[name], account, {
      provisioned_product_id = account.id
      id                     = account.account_id
    })
  }
}

resource "aws_organizations_account" "organization_accounts" {
  for_each = {
    for name, account in local.reconciled_units_accounts_data : name => account
    if !account.control_tower_managed
  }

  name                       = each.value.name
  email                      = each.value.email
  iam_user_access_to_billing = try(each.value.iam_user_access_to_billing, "ALLOW")
  role_name                  = try(coalesce(each.value.execution_role_name), null) != null ? each.value.execution_role_name : "OrganizationAccountAccessRole"

  # Find parent_id using a safer approach
  parent_id = each.value.ou_id

  tags = merge(local.tags, {
    Name            = each.value.name
    Classifications = join(" ", each.value.classifications)
    Environment     = each.value.environment
  })

  # Prevent automatic cleanup of accounts if deleted from state
  close_on_deletion = false

  # Prevent destructive changes
  lifecycle {
    ignore_changes = [
      name,
      email,
      iam_user_access_to_billing,
      role_name,
    ]
  }
}

locals {
  organization_aws_accounts = {
    for name, account in aws_organizations_account.organization_accounts : name =>
    merge(local.reconciled_units_accounts_data[name], account, {
      provisioned_product_id = null
      account_id             = account.id
    })
  }

  raw_aws_accounts = {
    for name, account in merge(local.controltower_aws_accounts, local.organization_aws_accounts) : name =>
    merge({
      for k, v in account : k => v if !startswith(k, "ou_") || contains(["ou_id", "ou_name"], k)
      }, {
      account_name = account.name
      root_account = (account.account_id == local.account_id)
      domain       = try(coalesce(account.domain), local.domains[account.environment], local.domains[local.environment])
    })
  }
}

data "assert_test" "accounts_contain_valid_environment" {
  for_each = local.raw_aws_accounts

  test  = contains(keys(local.domains), each.value.environment)
  throw = "Account ${each.key} does not contain a supported domain environment:\n${yamlencode(each.value)}"
}

locals {
  normalized_aws_account_names = {
    for name, account in local.raw_aws_accounts : name => replace(account.account_name, " ", "")
  }

  aws_account_network_names = {
    for name, normalized_name in local.normalized_aws_account_names : name =>
    try(coalesce(local.raw_aws_accounts[name].network_name), lower(replace(normalized_name, "_", "-")))
  }

  aws_account_execution_role_arns = {
    for name, account in local.raw_aws_accounts : name => try(coalesce(account.execution_role_name), null) != null ?
    format("arn:%s:iam::%s:role/%s", local.partition, account.account_id, account.execution_role_name) : ""
  }


  aws_accounts = {
    for name, account in local.raw_aws_accounts : name => merge(account, {
      execution_role_arn = try(coalesce(account.execution_role_arn), local.aws_account_execution_role_arns[name], "")
      network_name       = local.aws_account_network_names[name]
      json_key           = try(coalesce(account.json_key), replace(local.normalized_aws_account_names[name], "-", "_"))
      subdomain          = (!contains(local.live_environments, account.environment) || startswith(account.domain, local.aws_account_network_names[name])) ? account.domain : join(".", [local.aws_account_network_names[name], account.domain])
    })
  }

  all_classifications_all_accounts = distinct(flatten([
    for account in values(local.aws_accounts) : account.classifications
  ]))

  classified_accounts_by_id = {
    for classification in local.all_classifications_all_accounts : "${classification}_accounts" => {
      for account in values(local.aws_accounts) : account.account_id => account
      if contains(account.classifications, classification)
    }
  }

  classified_accounts_by_name = {
    for classification in local.all_classifications_all_accounts : "${classification}_accounts_by_name" => {
      for account in values(local.aws_accounts) : account.account_name => account
      if contains(account.classifications, classification)
    }
  }

  classified_accounts_by_json_key = {
    for classification in local.all_classifications_all_accounts : "${classification}_accounts_by_json_key" => {
      for account in values(local.aws_accounts) : account.json_key => account
      if contains(account.classifications, classification)
    }
  }

  # First, create the grouped version (always arrays)
  classified_accounts_by_environment_grouped = {
    for classification in local.all_classifications_all_accounts : classification => {
      for account in values(local.aws_accounts) : account.environment => account...
      if contains(account.classifications, classification)
    }
  }

  # Intermediate map to categorize single vs many
  classified_accounts_categorized = {
    for classification, env_map in local.classified_accounts_by_environment_grouped : classification => {
      single = {
        for env, accounts in env_map : env => accounts[0]
        if length(accounts) == 1
      }
      many = {
        for env, accounts in env_map : env => accounts
        if length(accounts) > 1
      }
    }
  }

  # Final output with dynamic keys
  classified_accounts_by_environment = merge([
    for classification, categorized in local.classified_accounts_categorized : {
      "${classification}_accounts_by_environment" = merge(
        categorized.single,
        categorized.many
      )
    }
  ]...)

  classified_accounts = merge(local.classified_accounts_by_id, local.classified_accounts_by_name, local.classified_accounts_by_json_key, local.classified_accounts_by_environment)
}
