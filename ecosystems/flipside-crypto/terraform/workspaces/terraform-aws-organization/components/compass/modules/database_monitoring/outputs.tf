output "role_name" {
  value = postgresql_role.datadog_role.name

  description = "Role name"
}

output "role_password" {
  value = aws_ssm_parameter.datadog_db_user_password.name

  description = "SSM path for the role password"
}
