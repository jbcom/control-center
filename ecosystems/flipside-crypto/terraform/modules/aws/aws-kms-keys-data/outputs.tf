output "aws_kms_keys" {
  value = local.aws_kms_key_data

  description = "AWS KMS keys for the account"
}