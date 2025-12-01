output "secrets" {
  value = try({
    data = {
      (var.config.role_id_key)   = local.secret_keeper_role_data["role_id"]
      (var.config.secret_id_key) = vault_approle_auth_backend_role_secret_id[0].this.secret_id
    }
  }, {})

  description = "Secrets, if any"
}