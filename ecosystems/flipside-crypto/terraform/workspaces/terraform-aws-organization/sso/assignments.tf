# ============================================================================
# Account Assignments - Explicit mappings
# ============================================================================

locals {
  # Get classified account sets from context
  infrastructure_account_ids = [
    for key, account in local.context.accounts_by_json_key :
    account.account_id
    if contains(lookup(account, "classifications", []), "infrastructure")
  ]

  analytics_account_ids = [
    for key, account in local.context.accounts_by_json_key :
    account.account_id
    if contains(lookup(account, "classifications", []), "analytics")
  ]

  data_platform_account_ids = [
    for key, account in local.context.accounts_by_json_key :
    account.account_id
    if contains(lookup(account, "classifications", []), "data_platform")
  ]

  serverless_account_ids = [
    for key, account in local.context.accounts_by_json_key :
    account.account_id
    if contains(lookup(account, "classifications", []), "serverless")
  ]

  # Combine data platform and serverless (unique)
  data_platform_and_serverless_ids = distinct(concat(local.data_platform_account_ids, local.serverless_account_ids))

  # All account IDs (excluding User-Joan and User-Liz)
  all_active_account_ids = [
    for key, account in local.context.accounts_by_json_key :
    account.account_id
    if !contains(["269429265333", "710162345443"], account.account_id)
  ]
}

# ============================================================================
# Root Group - Administrator on ALL accounts
# ============================================================================

resource "aws_ssoadmin_account_assignment" "root_admin_all" {
  for_each = toset(local.all_active_account_ids)

  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.aws_administrator_access.arn

  principal_type = "GROUP"
  principal_id   = aws_identitystore_group.sso_groups["root@flipsidecrypto.com"].group_id

  target_type = "AWS_ACCOUNT"
  target_id   = each.key
}

# ============================================================================
# Product Engineering - Administrator on infrastructure accounts
# ============================================================================

resource "aws_ssoadmin_account_assignment" "product_eng_infra_admin" {
  for_each = toset(local.infrastructure_account_ids)

  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.aws_administrator_access.arn

  principal_type = "GROUP"
  principal_id   = aws_identitystore_group.sso_groups["product-eng@flipsidecrypto.com"].group_id

  target_type = "AWS_ACCOUNT"
  target_id   = each.key
}

# ============================================================================
# Analytics - EngineeringAccess on analytics accounts
# ============================================================================

resource "aws_ssoadmin_account_assignment" "analytics_engineering" {
  for_each = toset(local.analytics_account_ids)

  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.engineering_access.arn

  principal_type = "GROUP"
  principal_id   = aws_identitystore_group.sso_groups["analytics@flipsidecrypto.com"].group_id

  target_type = "AWS_ACCOUNT"
  target_id   = each.key
}

# ============================================================================
# Data Platform - Administrator on data platform + serverless accounts
# ============================================================================

resource "aws_ssoadmin_account_assignment" "data_platform_admin" {
  for_each = toset(local.data_platform_and_serverless_ids)

  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.aws_administrator_access.arn

  principal_type = "GROUP"
  principal_id   = aws_identitystore_group.sso_groups["data-platform@flipsidecrypto.com"].group_id

  target_type = "AWS_ACCOUNT"
  target_id   = each.key
}
