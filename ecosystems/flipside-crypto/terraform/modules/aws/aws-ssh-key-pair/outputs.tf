output "key_pair_name" {
  value = join("", aws_key_pair.default_keypair.*.key_name)

  description = "Key pair name"
}

output "key_pair_path" {
  value = local.key_pair_path

  description = "Key pair path"
}

output "ssh_key_id" {
  value = join("", aws_key_pair.default_keypair.*.key_pair_id)

  description = "SSH key ID"
}

output "ssh_private_key" {
  value = local.private_key

  sensitive = true

  description = "SSH private key"
}

output "ssh_private_key_secret" {
  value = join("", aws_secretsmanager_secret.private_key.*.arn)

  description = "SSH private key secret"
}

output "ssh_private_key_path" {
  value = join("", local_sensitive_file.private.*.filename)

  description = "SSH private key path"
}

output "ssh_public_key" {
  value = local.public_key

  description = "SSH public key"
}

output "ssh_public_key_path" {
  value = join("", local_file.public.*.filename)

  description = "SSH public key path"
}

output "ssh_public_key_secret" {
  value = join("", aws_secretsmanager_secret.public_key.*.arn)

  description = "SSH public key secret"
}