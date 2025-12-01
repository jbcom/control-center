locals {
  group_name = coalesce(var.group.group_name, var.group_name)

  admins = distinct(flatten(concat(var.group.admins != null ? [
    var.group.admins,
    ] : [], var.group.external_admins != null ? [
    var.group.external_admins,
  ] : [])))

  group_admins = distinct(flatten(concat(var.group.group_admins != null ? [
    var.group.group_admins,
    ] : [], var.group.external_group_admins != null ? [
    var.group.external_group_admins,
  ] : [])))

  owners = distinct(flatten(concat(var.group.owners != null ? [
    var.group.owners,
    ] : [], var.group.external_owners != null ? [
    var.group.external_owners,
  ] : [])))

  group_owners = distinct(flatten(concat(var.group.group_owners != null ? [
    var.group.group_owners,
    ] : [], var.group.external_group_owners != null ? [
    var.group.external_group_owners,
  ] : [])))

  members = distinct(flatten(concat(var.group.members != null ? [
    var.group.members,
    ] : [], var.group.external_members != null ? [
    var.group.external_members,
  ] : [])))

  group_members = distinct(flatten(concat(var.group.group_members != null ? [
    var.group.group_members,
    ] : [], var.group.external_group_members != null ? [
    var.group.external_group_members,
  ] : [])))

  membership_lookup_data = merge({
    for username in local.members : username => {
      role = "MEMBER"
      type = "USER"
    }
    }, {
    for username in local.group_members : username => {
      role = "MEMBER"
      type = "GROUP"
    }
    }, {
    for username in local.admins : username => {
      role = "MANAGER"
      type = "USER"
    }
    }, {
    for username in local.group_admins : username => {
      role = "MANAGER"
      type = "GROUP"
    }
    }, {
    for username in local.owners : username => {
      role = "OWNER"
      type = "USER"
    }
    }, {
    for username in local.group_owners : username => {
      role = "OWNER"
      type = "GROUP"
    }
  })

  external_domain_membership_data = {
    for user_name, user_data in local.membership_lookup_data : user_name => merge(user_data, {
      primary_email = user_name
    }) if !endswith(try(split("@", user_name)[1], "flipsidecrypto.com"), "flipsidecrypto.com")
  }

  membership_raw_data = merge(local.external_domain_membership_data, {
    for user_name, user_data in var.users : user_name => merge(user_data, local.membership_lookup_data[user_name]) if lookup(local.membership_lookup_data, user_name, {}) != {}
  })

  membership_data = {
    for user_name, user_data in local.membership_raw_data : user_name => merge(user_data, {
      sso_only             = try(coalesce(user_data["sso_only"]), false)
      github_handle        = try(coalesce(user_data["github_handle"]), "")
      primary_email        = try(coalesce(user_data["primary_email"]), "")
      aws_sso_scim_user_id = try(coalesce(user_data["aws_sso_scim_user_id"]), "")
      slack_id             = try(coalesce(user_data["slack_id"]), "")
    })
  }

  enable_github  = try(coalesce(var.group.github_team_id), "") != ""
  enable_google  = try(coalesce(var.group.google_group_id), "") != ""
  enable_aws_sso = try(coalesce(var.group.aws_sso_scim_group_id), "") != ""
}

resource "github_team_membership" "default" {
  for_each = {
    for user_name, user_data in local.membership_data : user_name => user_data["github_handle"] if local.enable_github && !user_data["sso_only"] && user_data["github_handle"] != ""
  }

  team_id = var.group.github_team_id

  username = each.value
  role     = "maintainer"
}

resource "googleworkspace_group_members" "default" {
  count = local.enable_google ? 1 : 0

  group_id = var.group.google_group_id

  dynamic "members" {
    for_each = {
      for user_name, user_data in local.membership_data : user_name => user_data if !user_data["sso_only"] && user_data["primary_email"] != ""
    }

    content {
      email = members.value.primary_email
      role  = members.value.role
      type  = members.value.type
    }
  }
}

resource "aws-sso-scim_group_member" "default" {
  for_each = {
    for user_name, user_data in local.membership_data : user_name => user_data if local.enable_aws_sso && user_data["aws_sso_scim_user_id"] != ""
  }

  user_id  = each.value.aws_sso_scim_user_id
  group_id = var.group.aws_sso_scim_group_id
}

locals {
  slack_users = compact([
    for user_name, user_data in local.membership_data : user_data["slack_id"]
  ])
}

resource "slack_usergroup" "default" {
  count = var.group.enable_slack_group && length(local.slack_users) > 0 ? 1 : 0

  name  = coalesce(var.group.slack_group_name, local.group_name)
  users = local.slack_users
}