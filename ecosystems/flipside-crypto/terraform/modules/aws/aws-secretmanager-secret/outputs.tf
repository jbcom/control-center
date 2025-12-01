output "id" {
  value     = local.secret_id
  sensitive = true

  description = "Secrets Manager ID"
}

output "arn" {
  value = join("", aws_secretsmanager_secret.default.*.arn)

  description = "Secrets Manager ARN"
}

output "name" {
  value = join("", aws_secretsmanager_secret.default.*.name)

  description = "Secrets Manager name"
}