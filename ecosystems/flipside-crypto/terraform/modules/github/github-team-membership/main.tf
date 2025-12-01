resource "github_team_members" "this" {
  count = try(coalesce(var.config.github_team_id), null) != null ? 1 : 0

  team_id = var.config.github_team_id

  dynamic "members" {
    for_each = toset(var.membership.github_team_members)

    content {
      username = members.key
      role     = "maintainer"
    }
  }
}