resource "aws_iam_user" "this" {
  name                 = local.username
  path                 = "/"
  force_destroy        = false
  permissions_boundary = ""

  tags = local.tags
}

resource "aws_iam_user_login_profile" "this" {
  user                    = aws_iam_user.this.name
  pgp_key                 = "keybase:flipsidecrypto"
  password_length         = var.password_length
  password_reset_required = var.password_reset_required

  # TODO: Remove once https://github.com/hashicorp/terraform-provider-aws/issues/23567 is resolved
  lifecycle {
    ignore_changes = [password_reset_required]
  }
}

resource "aws_iam_access_key" "this" {
  user = aws_iam_user.this.name
}

resource "aws_iam_user_ssh_key" "this" {
  count = var.attach_key_pair ? 1 : 0

  username   = aws_iam_user.this.name
  encoding   = "SSH"
  public_key = join("", module.key-pair.*.ssh_public_key)
}

resource "aws_iam_user_policy_attachment" "this" {
  for_each = toset(local.policies)

  user       = aws_iam_user.this.name
  policy_arn = each.key
}

resource "gpg_private_key" "this" {
  count = var.generate_gpg_key ? 1 : 0

  name     = local.username
  email    = "${local.username}@flipsidecrypto.com"
  rsa_bits = 4096
}

resource "github_user_gpg_key" "this" {
  count = var.generate_gpg_key ? 1 : 0

  armored_public_key = join("", gpg_private_key.this.*.public_key)
}

resource "github_actions_organization_secret" "access-key" {
  count = var.save_secrets_to_github ? 1 : 0

  secret_name     = replace(format("%s_access_key", var.username), "-", "_")
  visibility      = "private"
  plaintext_value = aws_iam_access_key.this.id
}

resource "github_actions_organization_secret" "secret-key" {
  count = var.save_secrets_to_github ? 1 : 0

  secret_name     = replace(format("%s_secret_key", var.username), "-", "_")
  visibility      = "private"
  plaintext_value = aws_iam_access_key.this.secret
}

resource "github_actions_organization_secret" "gpg-public-key" {
  count = (var.generate_gpg_key && var.save_secrets_to_github) ? 1 : 0

  secret_name     = replace(format("%s_gpg_public_key", var.username), "-", "_")
  visibility      = "private"
  plaintext_value = join("", gpg_private_key.this.*.public_key)
}

resource "github_actions_organization_secret" "gpg-private-key" {
  count = (var.generate_gpg_key && var.save_secrets_to_github) ? 1 : 0

  secret_name     = replace(format("%s_gpg_private_key", var.username), "-", "_")
  visibility      = "private"
  plaintext_value = join("", gpg_private_key.this.*.private_key)
}

module "key-pair" {
  count = var.attach_key_pair ? 1 : 0

  source = "../../../../terraform-organization-administration/modules/aws-ssh-key-pair"

  key_pair_name = local.username

  write_key_pair_to_file   = var.write_key_pair_to_file
  write_key_pair_to_github = var.write_key_pair_to_github

  tags = local.tags
}

locals {
  ssm_parameters = merge({
    access_key        = aws_iam_access_key.this.id
    secret_access_key = aws_iam_access_key.this.secret
    }, var.attach_key_pair ? {
    ssh_public_key  = module.key-pair.0.ssh_public_key
    ssh_private_key = module.key-pair.0.ssh_private_key
  } : {})
}

module "parameter-store" {
  source  = "cloudposse/ssm-parameter-store/aws"
  version = "0.13.0"

  parameter_write = [
    for parameter_name, parameter_value in local.ssm_parameters : {
      name        = "/bots/${local.username}/${parameter_name}"
      value       = parameter_value
      type        = "SecureString"
      overwrite   = "true"
      description = "Managed by Terraform"
    }
  ]

  context = var.context
}

resource "null_resource" "cluster" {
  count = var.save_to_aws_profile ? 1 : 0

  triggers = {
    profile_name          = local.username
    aws_access_key        = aws_iam_access_key.this.id
    aws_secret_access_key = aws_iam_access_key.this.secret
  }

  provisioner "local-exec" {
    command = "${path.module}/bin/add_aws_profile.sh"

    environment = {
      PROFILE_NAME          = self.triggers.profile_name
      AWS_ACCESS_KEY        = self.triggers.aws_access_key
      AWS_SECRET_ACCESS_KEY = self.triggers.aws_secret_access_key
    }
  }
}