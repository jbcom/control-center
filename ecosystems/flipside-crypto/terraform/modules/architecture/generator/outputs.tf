output "records" {
  value = {
    guardduty = {
      configuration     = local.guardduty_configuration
      security_accounts = local.security_accounts_execution_role_arn_map
      accounts = {
        security = local.security_accounts_data
        members  = local.member_accounts_data
      }
    }

    ram_shares = local.ram_shares
  }

  description = "Records data"
}

output "pipeline" {
  value = module.pipeline

  description = "Pipeline data"
}