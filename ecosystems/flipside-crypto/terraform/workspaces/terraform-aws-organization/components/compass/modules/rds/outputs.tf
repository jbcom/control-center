output "db_password" {
  value     = random_password.master.result
  sensitive = true
}

output "db_user" {
  value     = module.aurora.cluster_master_username
  sensitive = true
}

output "db_write_host" {
  value     = module.aurora.cluster_endpoint
  sensitive = true
}

output "db_port" {
  value     = module.aurora.cluster_port
  sensitive = false
}

output "db_write_url" {
  value     = "postgresql://${module.aurora.cluster_master_username}:${random_password.master.result}@${module.aurora.cluster_endpoint}:${module.aurora.cluster_port}"
  sensitive = true
}

output "ssm_arn_app_db_write_url" {
  value = aws_ssm_parameter.app_db_write_url.arn
}
