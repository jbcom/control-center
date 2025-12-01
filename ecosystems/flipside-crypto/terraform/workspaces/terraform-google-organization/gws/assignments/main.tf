# Core data processing and transformations
locals {
  # Primary group assignments from context
  group_assignments = local.context.gws.assignments.groups

  # Create efficient lookup maps
  groups_by_email = local.context.gws.groups

  # Create interim lookup: group keys to their actual email addresses
  group_key_to_email = {
    for group_key, group_config in local.group_assignments :
    group_key => try(group_config.email, group_key)
  }

  # Process assignments with resolved group IDs for efficiency
  processed_assignments = {
    for group_key, group_config in local.group_assignments :
    group_key => {
      group_id = local.groups_by_email[local.group_key_to_email[group_key]].id
      members  = group_config.members
    }
  }

  # Flatten assignments for individual membership resources (shared pattern)
  flattened_memberships = merge(flatten([
    for group_key, group_config in local.processed_assignments : {
      for member_email, member_config in group_config.members :
      "${group_key}//${member_email}" => {
        group_key    = group_key
        group_id     = group_config.group_id
        member_email = member_email
        member_role  = member_config.type == "GROUP" ? null : member_config.role
        member_type  = member_config.type
      }
    }
  ])...)
}

# Create individual Google Workspace group memberships (aligned with AWS pattern)
resource "googleworkspace_group_member" "managed" {
  for_each = local.flattened_memberships

  group_id = each.value.group_id
  email    = each.value.member_email
  role     = each.value.member_role
  type     = each.value.member_type
}

# Read existing group memberships from Google Workspace
data "googleworkspace_group_members" "all" {
  for_each                   = local.processed_assignments
  group_id                   = each.value.group_id
  include_derived_membership = true
}

# AWS SSO configuration
data "aws_ssoadmin_instances" "selected" {}

locals {
  identity_store_id = tolist(data.aws_ssoadmin_instances.selected.identity_store_ids)[0]
}

data "aws_identitystore_users" "selected" {
  identity_store_id = local.identity_store_id
}

locals {
  # Create a map of user emails to their IDs
  users_by_email = {
    for user in data.aws_identitystore_users.selected.users :
    user.user_name => user.user_id
  }
}

# Create AWS Identity Store groups
resource "aws_identitystore_group" "managed" {
  for_each = local.processed_assignments

  display_name      = each.key
  description       = "Managed by Terraform"
  identity_store_id = local.identity_store_id
}

locals {
  # Combine managed memberships and discovered memberships for AWS SSO sync
  # This ensures we sync both Terraform-managed and UI-managed members
  all_google_memberships = merge(
    # Terraform-managed memberships
    {
      for key, membership in local.flattened_memberships :
      "${membership.group_key}//${membership.member_email}" => {
        group_key    = membership.group_key
        member_email = membership.member_email
      }
    },
    # UI-managed memberships discovered via data source
    merge(flatten([
      for group_key, group_data in data.googleworkspace_group_members.all : {
        for member in group_data.members :
        "${group_key}//${member.email}" => {
          group_key    = group_key
          member_email = member.email
        }
        # Only include if not already in managed memberships
        if !contains(keys(local.flattened_memberships), "${group_key}//${member.email}")
      }
    ])...)
  )

  # Create AWS SSO memberships for all Google members that exist in AWS
  aws_memberships = {
    for key, membership in local.all_google_memberships :
    key => {
      group_id  = aws_identitystore_group.managed[membership.group_key].group_id
      member_id = local.users_by_email[membership.member_email]
    }
    if contains(keys(local.users_by_email), membership.member_email)
  }
}

# Create individual AWS Identity Store group memberships (same pattern as Google)
resource "aws_identitystore_group_membership" "managed" {
  for_each = local.aws_memberships

  identity_store_id = local.identity_store_id
  group_id          = each.value.group_id
  member_id         = each.value.member_id
}
