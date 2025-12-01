locals {
  tags = {
    Name      = "${var.name}-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}

resource "aws_ssm_parameter" "password" {
  name        = "/${var.name}/${var.env}/db/password/main"
  description = "RDS Password Main"
  type        = "SecureString"
  value       = var.db_password

  tags = local.tags
}

resource "aws_ssm_parameter" "user" {
  name        = "/${var.name}/${var.env}/db/user/main"
  description = "RDS User Main"
  type        = "SecureString"
  value       = var.db_user

  tags = local.tags
}

resource "aws_ssm_parameter" "host" {
  name        = "/${var.name}/${var.env}/db/host/write"
  description = "RDS Write Host"
  type        = "SecureString"
  value       = var.db_write_host

  tags = local.tags
}

resource "aws_ssm_parameter" "port" {
  name        = "/${var.name}/${var.env}/db/port"
  description = "RDS Port"
  type        = "SecureString"
  value       = var.db_port

  tags = local.tags
}

resource "aws_ssm_parameter" "db_write_url" {
  name        = "/${var.name}/${var.env}/db/url/write"
  description = "RDS Write Url"
  type        = "SecureString"
  value       = var.db_write_url

  tags = local.tags
}