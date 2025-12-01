output "secrets" {
  value = local.secrets_data

  sensitive = true

  description = "Secrets data"
}
