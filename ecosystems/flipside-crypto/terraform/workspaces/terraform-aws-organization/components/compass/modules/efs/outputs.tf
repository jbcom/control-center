output "efs_id" {
  value = aws_efs_file_system.efs.id
}

output "efs_name" {
  value = aws_efs_file_system.efs.tags.Name
}