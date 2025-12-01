output "id" {
  value     = local.secret_id
  sensitive = true

  description = "DSN Secrets Manager ID"
}