locals {
  repository_permissions = {
    pull     = var.config.pull_repositories
    push     = var.config.push_repositories
    maintain = var.config.maintain_repositories
    triage   = var.config.triage_repositories
    admin    = var.config.admin_repositories
  }

  repository_names = distinct(compact(flatten([
    for _, repository_names in local.repository_permissions : repository_names
  ])))
}

resource "github_team_repository" "this" {
  for_each = {
    for repository_name in local.repository_names : repository_name => one([
      for permission, repository_names in local.repository_permissions : permission
      if contains(repository_names, repository_name)
    ]) if try(coalesce(var.config.github_team_id), null) != null
  }

  team_id    = var.config.github_team_id
  repository = each.key
  permission = each.value
}