output "role_arn" {
  value = join("", aws_iam_role.default.*.arn)

  description = "Role ARN"
}

output "role_name" {
  value = join("", aws_iam_role.default.*.name)

  description = "Role name"
}