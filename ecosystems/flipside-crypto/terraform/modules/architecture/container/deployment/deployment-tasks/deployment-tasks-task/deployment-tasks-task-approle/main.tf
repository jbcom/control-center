locals {
  secret_keeper_role_data = jsondecode(file("${path.module}/files/secret-keeper-role.json"))
}

resource "vault_approle_auth_backend_role_secret_id" "this" {
  count = var.config.enabled ? 1 : 0

  backend   = local.secret_keeper_role_data["backend"]
  role_name = local.secret_keeper_role_data["role_name"]
}