locals {
  units = {
    for unit_name, unit_config in local.context.units : unit_name => merge(unit_config, {
      environment = try(coalesce(unit_config.environment), local.environment)
      classifications = distinct(concat(try(compact(unit_config.classifications), []), [
        lower(replace(unit_name, " ", "_")),
      ]))
      accounts = {
        for account_name, account_config in unit_config.accounts : account_name => merge(account_config, {
          organizational_unit = unit_name
        })
      }
    })
  }

  unit_classifications = {
    for unit, config in local.units : unit => config.classifications
  }

  unit_environments = {
    for unit, config in local.units : unit => config.environment
  }

  unit_name_to_key_map = {
    for unit_key, unit_config in local.context.units : unit_config.name => unit_key
  }

  unit_accounts = merge(flatten([
    for unit_config in values(local.units) : unit_config.accounts
  ])...)
}
