output "vault_address" {
  value = format("https://%s:8200", local.shared_san)

  description = "Vault address"
}

output "vault_role_arn" {
  value = module.vault_server_role.service_account_role_arn

  description = "Vault role ARN"
}

output "vault_role_name" {
  value = module.vault_server_role.service_account_role_name

  description = "Vault role name"
}