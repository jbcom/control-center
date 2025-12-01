locals {
  tags = {
    Name      = "${var.name}-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}


resource "aws_ssm_parameter" "sentry_dsn_rpc" {
  name        = "/${var.name}/${var.env}/monitoring/sentry/dsn_rpc"
  description = "Sentry DSN for the RPC service"
  type        = "SecureString"
  value       = var.sentry_dsn_rpc

  tags = local.tags
}


resource "aws_ssm_parameter" "sentry_dsn_workers" {
  name        = "/${var.name}/${var.env}/monitoring/sentry/dsn_workers"
  description = "Sentry DSN for the Workers service"
  type        = "SecureString"
  value       = var.sentry_dsn_workers

  tags = local.tags
}


resource "aws_ssm_parameter" "datadog_api_key" {
  name        = "/${var.name}/${var.env}/monitoring/datadog/api_key"
  description = "DataDog API Key"
  type        = "SecureString"
  value       = var.datadog_api_key

  tags = local.tags
}