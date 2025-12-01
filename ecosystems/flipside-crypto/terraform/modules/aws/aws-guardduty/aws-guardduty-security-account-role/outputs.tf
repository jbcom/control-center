output "arn" {
  value = aws_iam_role.GuardDutyTerraformSecurityAcctRole.arn

  description = "Role ARN"
}

output "name" {
  value = aws_iam_role.GuardDutyTerraformSecurityAcctRole.name

  description = "Role name"
}
