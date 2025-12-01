output "json" {
  description = "JSON body of the KMS key policy document"
  value       = data.aws_iam_policy_document.this.json
}

output "policy_arn" {
  description = "ARN of the created KMS key policy (if kms_policy_enabled is true)"
  value       = var.kms_policy_enabled ? aws_kms_key_policy.default[0].id : null
}
