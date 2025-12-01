output "dsn" {
  value = module.dsn.id

  sensitive = true

  description = "DSN Secrets Manager ID"
}

output "url" {
  value = module.url.id

  sensitive = true

  description = "URL Secrets Manager ID"
}