output "arn" {
  value = aws_iam_role.GuardDutyTerraformLoggingAcctRole.arn

  description = "Role ARN"
}

output "name" {
  value = aws_iam_role.GuardDutyTerraformLoggingAcctRole.name

  description = "Role name"
}
