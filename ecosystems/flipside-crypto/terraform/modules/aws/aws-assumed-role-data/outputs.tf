output "use_assumed_role" {
  value = local.should_use_assume_role ? true : false

  description = "Whether to assume a role"
}

output "assume_role_arn" {
  value = local.should_use_assume_role ? data.aws_iam_session_context.current.issuer_arn : ""

  description = "Assumed role ARN"
}