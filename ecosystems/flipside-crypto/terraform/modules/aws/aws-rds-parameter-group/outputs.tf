output "db_parameter_group_name" {
  value = aws_db_parameter_group.this.name

  description = "DB parameter group name"
}

output "cluster_parameter_group_name" {
  value = join("", aws_rds_cluster_parameter_group.this.*.name)

  description = "DB cluster parameter group name"
}