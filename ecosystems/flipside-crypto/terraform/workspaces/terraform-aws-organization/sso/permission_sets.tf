# ============================================================================
# Permission Sets - Explicit definitions
# ============================================================================

# AWSAdministratorAccess
resource "aws_ssoadmin_permission_set" "aws_administrator_access" {
  instance_arn     = local.sso_instance_arn
  name             = "AWSAdministratorAccess"
  description      = "Provides full access to AWS services and resources"
  session_duration = "PT1H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_admin_billing_conductor" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSBillingConductorReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_administrator_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_admin_billing_readonly" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_administrator_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_admin_administrator" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_administrator_access.arn
}

# EngineeringAccess
resource "aws_ssoadmin_permission_set" "engineering_access" {
  instance_arn     = local.sso_instance_arn
  name             = "EngineeringAccess"
  description      = "Allow engineering access to the account"
  session_duration = "PT8H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "eng_cloud9" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSCloud9User"
  permission_set_arn = aws_ssoadmin_permission_set.engineering_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "eng_glue" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess"
  permission_set_arn = aws_ssoadmin_permission_set.engineering_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "eng_athena" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
  permission_set_arn = aws_ssoadmin_permission_set.engineering_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "eng_readonly" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.engineering_access.arn
}

resource "aws_ssoadmin_permission_set_inline_policy" "engineering_access_inline" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.engineering_access.arn
  inline_policy      = local.permission_sets_config.EngineeringAccess.inline_policy
}

# ============================================================================
# Additional Permission Sets
# ============================================================================

# AWSOrganizationsFullAccess
resource "aws_ssoadmin_permission_set" "aws_organizations_full_access" {
  instance_arn     = local.sso_instance_arn
  name             = "AWSOrganizationsFullAccess"
  description      = "Provides full access to AWS Organizations"
  session_duration = "PT1H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_orgs_full" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSOrganizationsFullAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_organizations_full_access.arn
}

# AWSPowerUserAccess
resource "aws_ssoadmin_permission_set" "aws_power_user_access" {
  instance_arn     = local.sso_instance_arn
  name             = "AWSPowerUserAccess"
  description      = "Provides full access to AWS services and resources, but does not allow management of Users and groups"
  session_duration = "PT1H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_power_billing_conductor" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSBillingConductorReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_power_user_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_power_billing_readonly" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_power_user_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_power_power_user" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_power_user_access.arn
}

# AWSReadOnlyAccess
resource "aws_ssoadmin_permission_set" "aws_read_only_access" {
  instance_arn     = local.sso_instance_arn
  name             = "AWSReadOnlyAccess"
  description      = "This policy grants permissions to view resources and basic metadata across all AWS services"
  session_duration = "PT1H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "aws_readonly_view_only" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_read_only_access.arn
}

# AWSServiceCatalogAdminFullAccess
resource "aws_ssoadmin_permission_set" "aws_service_catalog_admin" {
  instance_arn     = local.sso_instance_arn
  name             = "AWSServiceCatalogAdminFullAccess"
  description      = "Provides full access to AWS Service Catalog admin capabilities"
  session_duration = "PT1H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "svc_catalog_admin" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSServiceCatalogAdminFullAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_service_catalog_admin.arn
}

# AWSServiceCatalogEndUserAccess
resource "aws_ssoadmin_permission_set" "aws_service_catalog_end_user" {
  instance_arn     = local.sso_instance_arn
  name             = "AWSServiceCatalogEndUserAccess"
  description      = "Provides access to the AWS Service Catalog end user console"
  session_duration = "PT1H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "svc_catalog_end_user" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSServiceCatalogEndUserFullAccess"
  permission_set_arn = aws_ssoadmin_permission_set.aws_service_catalog_end_user.arn
}

resource "aws_ssoadmin_permission_set_inline_policy" "service_catalog_end_user_inline" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.aws_service_catalog_end_user.arn
  inline_policy      = local.permission_sets_config.AWSServiceCatalogEndUserAccess.inline_policy
}

# BillingAccess
resource "aws_ssoadmin_permission_set" "billing_access" {
  instance_arn     = local.sso_instance_arn
  name             = "BillingAccess"
  description      = "Allow billing access to the account"
  session_duration = "PT8H"
  tags             = local.tags
}

resource "aws_ssoadmin_permission_set_inline_policy" "billing_access_inline" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.billing_access.arn
  inline_policy      = local.permission_sets_config.BillingAccess.inline_policy
}

# FlipsideDiscordMgmt
resource "aws_ssoadmin_permission_set" "flipside_discord_mgmt" {
  instance_arn     = local.sso_instance_arn
  name             = "FlipsideDiscordMgmt"
  description      = "Discord management permission set for Route53 access"
  session_duration = "PT12H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "discord_readonly" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.flipside_discord_mgmt.arn
}

resource "aws_ssoadmin_permission_set_inline_policy" "discord_mgmt_inline" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.flipside_discord_mgmt.arn
  inline_policy      = local.permission_sets_config.FlipsideDiscordMgmt.inline_policy
}

# PowerUserAccess
resource "aws_ssoadmin_permission_set" "power_user_access" {
  instance_arn     = local.sso_instance_arn
  name             = "PowerUserAccess"
  description      = "Allow power user access to non-infrastructure accounts"
  session_duration = "PT8H"
  tags             = local.tags
}

resource "aws_ssoadmin_managed_policy_attachment" "power_cloud9" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSCloud9User"
  permission_set_arn = aws_ssoadmin_permission_set.power_user_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "power_codepipeline" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AWSCodePipeline_FullAccess"
  permission_set_arn = aws_ssoadmin_permission_set.power_user_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "power_iam_readonly" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.power_user_access.arn
}

resource "aws_ssoadmin_managed_policy_attachment" "power_power_user" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
  permission_set_arn = aws_ssoadmin_permission_set.power_user_access.arn
}
