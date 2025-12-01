module "github-aws-oidc" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-oidc-github"

  context = local.context
}

resource "github_actions_organization_secret" "github-aws-oidc" {
  secret_name     = "AWS_OIDC_ROLE_ARN"
  visibility      = "private"
  plaintext_value = module.github-aws-oidc.arn
}

# resource "snowflake_saml2_integration" "google_sso" {
#   name = "GOOGLE_SSO"
#
#   enabled = true
#
#   saml2_provider  = "CUSTOM"
#   saml2_issuer    = local.snowflake_sso_data["issuer"]
#   saml2_sso_url   = local.snowflake_sso_data["sso_url"]
#   saml2_x509_cert = local.snowflake_sso_data["certificate"]
#
#   saml2_sp_initiated_login_page_label = "GOOGLE_SSO"
#   saml2_enable_sp_initiated           = true
# }

resource "aws_iam_saml_provider" "googleworkspace" {
  name                   = "GoogleWorkspace"
  saml_metadata_document = local.googleworkspace_idp_data

  tags = merge(local.context["tags"], {
    Name = "GoogleWorkspace"
  })
}

module "googleworkspace_sso_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-saml"
  version = "5.37.1"

  create_role = true

  role_name = "GoogleWorkspaceSSO"

  tags = merge(local.context["tags"], {
    Name = "GoogleWorkspace"
  })

  provider_id = aws_iam_saml_provider.googleworkspace.id

  role_policy_arns = [
    "arn:aws:iam::aws:policy/AdministratorAccess",
  ]

  number_of_role_policy_arns = 1
}

locals {
  records_config = merge({
    github = module.github-aws-oidc,
    hevo_postgres = {
      readonly_user = {
        username    = module.hevo_readonly_user.username,
        secret_name = module.hevo_readonly_user.secret_name,
        secret_arn  = module.hevo_readonly_user.secret_arn,
        database    = module.hevo_readonly_user.database,
        schema      = module.hevo_readonly_user.schema,
        host        = "product-eng-velocity-mark-2.cik7nbaqdhks.us-east-1.rds.amazonaws.com",
        port        = 5432
      }
    }
  })
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspace_dir}"

  log_file_name = "permanent_record.log"
}
