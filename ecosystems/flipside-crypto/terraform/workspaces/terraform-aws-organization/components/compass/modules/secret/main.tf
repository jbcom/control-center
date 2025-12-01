resource "aws_secretsmanager_secret" "default" {
  count = var.enabled ? 1 : 0

  name = var.name

  kms_key_id = var.kms_key_arn

  recovery_window_in_days = 0

  force_overwrite_replica_secret = true

  tags = var.tags
}

locals {
  secret_id = join("", aws_secretsmanager_secret.default.*.id)
}

resource "aws_secretsmanager_secret_version" "default" {
  count = var.enabled ? 1 : 0

  secret_id     = local.secret_id
  secret_string = var.secret
}

resource "aws_secretsmanager_secret_policy" "default" {
  count = var.enabled && var.policy != null ? 1 : 0

  secret_arn = join("", aws_secretsmanager_secret.default.*.arn)

  policy = var.policy
}