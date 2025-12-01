resource "googleworkspace_group_members" "this" {
  count = try(coalesce(var.config.google_group_id), null) != null ? 1 : 0

  group_id = var.config.google_group_id

  dynamic "members" {
    for_each = toset(var.membership.google_user_owners)

    content {
      email = members.key
      role  = "OWNER"
    }
  }

  dynamic "members" {
    for_each = toset(var.membership.google_user_admins)

    content {
      email = members.key
      role  = "MANAGER"
    }
  }

  dynamic "members" {
    for_each = toset(var.membership.google_user_members)

    content {
      email = members.key
    }
  }

  dynamic "members" {
    for_each = toset(var.membership.google_group_owners)

    content {
      email = members.key
      role  = "OWNER"
      type  = "GROUP"
    }
  }

  dynamic "members" {
    for_each = toset(var.membership.google_group_admins)

    content {
      email = members.key
      role  = "MANAGER"
      type  = "GROUP"
    }
  }

  dynamic "members" {
    for_each = toset(var.membership.google_group_members)

    content {
      email = members.key
      type  = "GROUP"
    }
  }
}