resource "random_password" "secret_password" {
  for_each = var.config.random

  length = each.value.length

  lower            = each.value.lower
  min_lower        = each.value.min_lower
  min_numeric      = each.value.min_numeric
  min_special      = each.value.min_special
  min_upper        = each.value.min_upper
  numeric          = each.value.numeric
  override_special = each.value.override_special
  special          = each.value.special
  upper            = each.value.upper
}

resource "aws_secretsmanager_secret" "password" {
  for_each = random_password.secret_password

  name_prefix = "/ecs/${trimprefix(var.secret_manager_name_prefix, "/")}/${each.key}"

  recovery_window_in_days = 0

  tags = var.context["tags"]
}

resource "aws_secretsmanager_secret_version" "password" {
  for_each = aws_secretsmanager_secret.password

  secret_id = each.value.id

  secret_string = random_password.secret_password[each.key].result
}

module "secret_vendors_data" {
  source = "../../../secrets/vendors/vendors-remote"
}

resource "aws_secretsmanager_secret" "vendor" {
  for_each = var.config.vendors

  name_prefix = "/ecs/${trimprefix(var.secret_manager_name_prefix, "/")}/${each.key}"

  recovery_window_in_days = 0

  tags = var.context["tags"]
}

resource "aws_secretsmanager_secret_version" "vendor" {
  for_each = aws_secretsmanager_secret.vendor

  secret_id = each.value.id

  secret_string = module.secret_vendors_data.credentials[var.config.vendors[each.key]]
}

module "secrets_data" {
  source = "./secrets-data"

  config = var.config

  secrets_dir = var.secrets_dir

  rel_to_root = var.rel_to_root

  context = var.context

  debug_file = var.debug_file
}

resource "aws_secretsmanager_secret" "default" {
  for_each = try(nonsensitive(module.secrets_data.secrets), module.secrets_data.secrets)

  name_prefix = "/ecs/${trimprefix(var.secret_manager_name_prefix, "/")}/${each.key}"

  recovery_window_in_days = 0

  tags = var.context["tags"]
}

resource "aws_secretsmanager_secret_version" "default" {
  for_each = aws_secretsmanager_secret.default

  secret_id = each.value.id

  secret_string = trimsuffix(trimprefix(module.secrets_data.secrets[each.key], try(var.config.trim[each.key].prefix, "")), try(var.config.trim[each.key].suffix, ""))
}

locals {
  ecs_secret_data = merge(aws_secretsmanager_secret.password, aws_secretsmanager_secret.vendor, aws_secretsmanager_secret.default)
}

data "aws_iam_policy_document" "secrets_retrieval_policy_document" {
  statement {
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]

    resources = ["*"]
  }

  statement {
    actions = [
      "kms:ListKeys",
      "kms:GenerateRandom",
    ]

    resources = ["*"]
  }

  statement {
    actions = [
      "ssm:GetParameter*",
    ]

    resources = [
      for _, secret_data in local.ecs_secret_data : secret_data["arn"]
    ]
  }

  statement {
    actions = [
      "ssm:DescribeParameters",
    ]

    resources = ["*"]
  }

  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]

    resources = ["*"]
  }
}

moved {
  from = module.policy.aws_iam_policy.default[0]
  to   = aws_iam_policy.default[0]
}

resource "aws_iam_policy" "default" {
  count = var.create_policy && local.ecs_secret_data != {} ? 1 : 0

  name = "${var.context.id}-${var.policy_name}"

  policy = data.aws_iam_policy_document.secrets_retrieval_policy_document.json

  tags = merge(var.context["tags"], {
    Name = "${var.context.id}-${var.policy_name}"
  })
}