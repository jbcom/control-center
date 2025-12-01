output "context" {
  value = merge(local.context, {
    admin_account_ids = keys(local.context.networked_accounts)

    admin_principals = tolist(setunion(toset(local.context.admin_bot_users), toset([
      for account in local.context.networked_accounts : account["execution_role_arn"]
      if try(coalesce(account["execution_role_arn"]), null) != null
    ])))

    account_bindings = {
      for json_key, account_data in local.context.networked_accounts_by_json_key : json_key =>
      try(coalesce(account_data["execution_role_arn"]), "")
    }
  })

  sensitive = true

  description = "Aggregated AWS organization data"
}
