module "sso_roles_data" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-sso-roles-data"
}

locals {
  sso_roles = module.sso_roles_data.roles
  grantees  = values(local.sso_roles)
}

module "kms" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-kms-key"

  kms_key_name        = "global"
  kms_key_description = "Global KMS key for organization wide secure operations"

  organization_id             = aws_organizations_organization.this.id
  include_organization_policy = true

  include_cloudtrail_policy      = true
  include_cloudwatch_logs_policy = true

  manage_kms_key_policy = true

  kms_key_aliases = [
    "internal-organization-tooling",
    "terraform-organization",
  ]

  account_ids = [
    local.account_id,
  ]

  grantees = local.grantees

  tags = local.context["tags"]
}

locals {
  kms_key_arn = module.kms.arn
}

module "secrets_directory" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//secrets/kms-sops-directory"

  kms_key_arn = local.kms_key_arn

  save_files = true

  rel_to_root = local.rel_to_root
}

