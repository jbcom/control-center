output "sentry_dsn_workers_arn" {
  value = aws_ssm_parameter.sentry_dsn_workers.arn
}

output "sentry_dsn_rpc_arn" {
  value = aws_ssm_parameter.sentry_dsn_rpc.arn
}

output "datadog_api_key_arn" {
  value = aws_ssm_parameter.datadog_api_key.arn
}