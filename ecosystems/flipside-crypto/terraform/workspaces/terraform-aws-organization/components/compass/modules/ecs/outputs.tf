output "cluster_name" {
  value = aws_ecs_cluster.cluster.name
}

output "ssm_arn_access_key_id" {
  value = aws_ssm_parameter.access_key_id.arn
}

output "ssm_arn_secret_access_key" {
  value = aws_ssm_parameter.secret_access_key.arn
}

output "ssm_arn_data_source_encryption_key" {
  value = aws_ssm_parameter.data_source_encryption_key.arn
}

output "iam_task_execution_role_name" {
  value = aws_iam_role.task_execution_role.name
}
