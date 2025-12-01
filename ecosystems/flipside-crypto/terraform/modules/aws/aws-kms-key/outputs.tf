output "key_id" {
  value       = aws_kms_key.default.id
  description = "KMS key ID"
}

output "arn" {
  value       = aws_kms_key.default.arn
  description = "KMS key ARN"
}

output "default_alias" {
  value       = try(aws_kms_alias.default.0.arn, "")
  description = "Default alias, if any"
}

output "policy_json" {
  value       = module.kms_key_policy.json
  description = "JSON body of the KMS key policy document"
}

output "policy_arn" {
  value       = module.kms_key_policy.policy_arn
  description = "ARN of the created KMS key policy (if kms_policy_enabled is true)"
}
