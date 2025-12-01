resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

locals {
  public_key  = chomp(tls_private_key.ssh_key.public_key_openssh)
  private_key = chomp(tls_private_key.ssh_key.private_key_pem)
}

resource "aws_key_pair" "default_keypair" {
  count = var.write_key_pair_to_aws ? 1 : 0

  key_name   = var.key_pair_name
  public_key = local.public_key
}

moved {
  from = aws_key_pair.default_keypair
  to   = aws_key_pair.default_keypair[0]
}

resource "local_file" "public" {
  count = var.write_key_pair_to_file ? 1 : 0

  content              = local.public_key
  filename             = "${local.key_pair_path}/${var.key_pair_name}.pub"
  file_permission      = "0644"
  directory_permission = "0700"
}

resource "local_sensitive_file" "private" {
  count = var.write_key_pair_to_file ? 1 : 0

  content              = local.private_key
  filename             = "${local.key_pair_path}/${var.key_pair_name}"
  file_permission      = "0600"
  directory_permission = "0700"
}

resource "github_user_ssh_key" "public" {
  count = var.write_key_pair_to_github ? 1 : 0

  title = var.key_pair_name
  key   = local.public_key
}

locals {
  secret_prefix = upper(replace(var.key_pair_name, "-", "_"))
}

resource "github_actions_organization_secret" "public_key" {
  count = var.write_key_pair_to_github ? 1 : 0

  secret_name     = "${local.secret_prefix}_SSH_PUBLIC_KEY"
  visibility      = "private"
  plaintext_value = local.public_key
}

resource "github_actions_organization_secret" "private_key" {
  count = var.write_key_pair_to_github ? 1 : 0

  secret_name     = "${local.secret_prefix}_SSH_PRIVATE_KEY"
  visibility      = "private"
  plaintext_value = local.private_key
}

resource "aws_secretsmanager_secret" "public_key" {
  count = var.save_secrets_to_aws ? 1 : 0

  name = "${var.secrets_manager_prefix}/${var.key_pair_name}/public_key"

  kms_key_id = var.kms_key_arn

  recovery_window_in_days = 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "public_key" {
  count = var.save_secrets_to_aws ? 1 : 0

  secret_id     = aws_secretsmanager_secret.public_key.0.id
  secret_binary = base64encode(local.public_key)
}

resource "aws_secretsmanager_secret" "private_key" {
  count = var.save_secrets_to_aws ? 1 : 0

  name = "${var.secrets_manager_prefix}/${var.key_pair_name}/private_key"

  kms_key_id = var.kms_key_arn

  recovery_window_in_days = 0

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "private_key" {
  count = var.save_secrets_to_aws ? 1 : 0

  secret_id     = aws_secretsmanager_secret.private_key.0.id
  secret_binary = base64encode(local.private_key)
}
