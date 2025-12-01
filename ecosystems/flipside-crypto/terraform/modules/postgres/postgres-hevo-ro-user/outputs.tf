output "username" {
  description = "The username of the Hevo read-only user"
  value       = postgresql_role.hevo_readonly_user.name
}

output "secret_arn" {
  description = "The ARN of the AWS Secrets Manager secret containing the password"
  value       = aws_secretsmanager_secret.hevo_readonly_password.arn
}

output "secret_name" {
  description = "The name of the AWS Secrets Manager secret containing the password"
  value       = aws_secretsmanager_secret.hevo_readonly_password.name
}

output "database" {
  description = "The database name that the user has access to"
  value       = var.database_name
}

output "schema" {
  description = "The schema name that the user has access to"
  value       = var.schema_name
}
