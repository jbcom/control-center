# ============================================================================
# SSO Workspace - AWS IAM Identity Center Configuration
# ============================================================================

locals {
  tags = local.context.tags

  # SSO instance is managed by AWS Control Tower
  sso_instance_arn  = tolist(data.aws_ssoadmin_instances.this.arns)[0]
  identity_store_id = tolist(data.aws_ssoadmin_instances.this.identity_store_ids)[0]

  # Permission sets configuration
  permission_sets_config = local.context.sso.permission_sets
}

# ============================================================================
# Data Sources
# ============================================================================

# Get SSO instance (managed by Control Tower)
data "aws_ssoadmin_instances" "this" {}

# Get all Google Workspace groups
data "googleworkspace_groups" "all" {}

# Get members for each Google Workspace group
data "googleworkspace_group_members" "all" {
  for_each = {
    for group in data.googleworkspace_groups.all.groups :
    group.email => group
  }

  group_id                   = each.value.id
  include_derived_membership = true
}

# ============================================================================
# SSO Groups - Create for ALL Google Workspace groups
# ============================================================================

resource "aws_identitystore_group" "sso_groups" {
  for_each = {
    for group in data.googleworkspace_groups.all.groups :
    group.email => group
    if !startswith(group.email, "AWS")
  }

  identity_store_id = local.identity_store_id
  display_name      = each.value.email
  description       = each.value.description != null && each.value.description != "" ? each.value.description : "Synced from Google Workspace"
}

# ============================================================================
# Group Memberships - Add Google users to groups
# ============================================================================

locals {
  # Flatten group memberships - only @flipsidecrypto.com users
  group_memberships = flatten([
    for group_email, members_data in data.googleworkspace_group_members.all : [
      for member in members_data.members : {
        group_email = group_email
        user_email  = member.email
        key         = "${group_email}::${member.email}"
      }
      if member.type == "USER" && endswith(member.email, "@flipsidecrypto.com") && !startswith(group_email, "AWS")
    ]
    if members_data.members != null
  ])

  group_memberships_map = {
    for membership in local.group_memberships :
    membership.key => membership
  }
}

# Get existing SSO users (synced from Google via SCIM)
data "aws_identitystore_user" "users" {
  for_each = toset([
    for membership in local.group_memberships :
    membership.user_email
  ])

  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "UserName"
      attribute_value = each.key
    }
  }
}

resource "aws_identitystore_group_membership" "memberships" {
  for_each = local.group_memberships_map

  identity_store_id = local.identity_store_id
  group_id          = aws_identitystore_group.sso_groups[each.value.group_email].group_id
  member_id         = data.aws_identitystore_user.users[each.value.user_email].user_id
}
