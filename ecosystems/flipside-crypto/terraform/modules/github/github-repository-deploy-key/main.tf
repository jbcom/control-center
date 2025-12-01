resource "tls_private_key" "deploy-key" {
  count = var.enabled ? 1 : 0

  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}

moved {
  from = tls_private_key.deploy-key
  to   = tls_private_key.deploy-key[0]
}

locals {
  private_key_pem            = join("", tls_private_key.deploy-key.*.private_key_pem)
  private_key_pem_base64_enc = base64encode(chomp(local.private_key_pem))

  public_key_pem            = join("", tls_private_key.deploy-key.*.public_key_pem)
  public_key_pem_base64_enc = base64encode(chomp(local.public_key_pem))

  public_key_openssh            = join("", tls_private_key.deploy-key.*.public_key_openssh)
  public_key_openssh_base64_enc = base64encode(chomp(local.public_key_openssh))
}

resource "github_repository_deploy_key" "deploy-key" {
  count = var.enabled ? 1 : 0

  title      = var.repository_name
  repository = var.repository_name
  key        = local.public_key_openssh
  read_only  = var.read_only
}

moved {
  from = github_repository_deploy_key.deploy-key
  to   = github_repository_deploy_key.deploy-key[0]
}

resource "github_actions_secret" "deploy-key" {
  count = var.enabled ? 1 : 0

  repository      = var.repository_name
  secret_name     = replace(upper("deploy_key_${var.repository_name}"), "-", "_")
  plaintext_value = local.private_key_pem_base64_enc
}

moved {
  from = github_actions_secret.deploy-key
  to   = github_actions_secret.deploy-key[0]
}

locals {
  ssm_path_prefix = "/repositories/${var.repository_name}"

  stored_params = [
    "public_key_openssh",
    "public_key_pem",
    "private_key_pem",
  ]
}

resource "aws_ssm_parameter" "param-public_key_openssh" {
  count = var.enabled ? 1 : 0

  name  = "${local.ssm_path_prefix}/public_key_openssh"
  type  = "SecureString"
  value = local.public_key_openssh_base64_enc

  tags = var.tags
}

moved {
  from = aws_ssm_parameter.param-public_key_openssh
  to   = aws_ssm_parameter.param-public_key_openssh[0]
}

resource "aws_ssm_parameter" "param-public_key_pem" {
  count = var.enabled ? 1 : 0

  name  = "${local.ssm_path_prefix}/public_key_pem"
  type  = "SecureString"
  value = local.public_key_pem_base64_enc

  tags = var.tags
}

moved {
  from = aws_ssm_parameter.param-public_key_pem
  to   = aws_ssm_parameter.param-public_key_pem[0]
}

resource "aws_ssm_parameter" "param-private_key_pem" {
  count = var.enabled ? 1 : 0

  name  = "${local.ssm_path_prefix}/private_key_pem"
  type  = "SecureString"
  value = local.private_key_pem_base64_enc

  tags = var.tags
}

moved {
  from = aws_ssm_parameter.param-private_key_pem
  to   = aws_ssm_parameter.param-private_key_pem[0]
}
