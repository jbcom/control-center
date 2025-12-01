output "bucket_name" {
  value = local.bucket_id

  description = "The GuardDuty findings bucket name"
}

output "bucket_arn" {
  value = local.bucket_arn

  description = "The GuardDuty findings bucket ARN"
}

output "kms_key_arn" {
  value = aws_kms_key.gd_key.arn

  description = "The GuardDuty KMS key ARN"
}