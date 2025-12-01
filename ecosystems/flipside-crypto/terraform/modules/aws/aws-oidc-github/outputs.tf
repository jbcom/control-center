output "name" {
  value = aws_iam_role.github.name

  description = "IAM role name"
}

output "arn" {
  value = aws_iam_role.github.arn

  description = "IAM role ARN"
}