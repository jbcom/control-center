resource "github_branch_protection" "this" {
  for_each = var.config.protection_rules

  repository_id = local.github_repository_name

  pattern                         = coalesce(each.value.pattern, each.key)
  enforce_admins                  = each.value.enforce_admins
  require_signed_commits          = each.value.require_signed_commits
  required_linear_history         = each.value.required_linear_history
  require_conversation_resolution = each.value.require_conversation_resolution

  dynamic "required_status_checks" {
    for_each = each.value["required_status_checks"] != {} ? [0] : []

    content {
      strict   = try(each.value["required_status_checks"]["strict"], false)
      contexts = try(each.value["required_status_checks"]["contexts"], [])
    }
  }

  dynamic "required_pull_request_reviews" {
    for_each = each.value["required_pull_request_reviews"] != {} ? [0] : []

    content {
      dismiss_stale_reviews  = lookup(each.value["required_pull_request_reviews"], "dismiss_stale_reviews", false)
      restrict_dismissals    = lookup(each.value["required_pull_request_reviews"], "restrict_dismissals", false)
      dismissal_restrictions = lookup(each.value["required_pull_request_reviews"], "dismissal_restrictions", [])
      pull_request_bypassers = [
        for actor in lookup(each.value["required_pull_request_reviews"], "pull_request_bypassers", []) : data.github_user.actor[actor]["node_id"]
      ]

      require_code_owner_reviews      = lookup(each.value["required_pull_request_reviews"], "require_code_owner_reviews", false)
      required_approving_review_count = lookup(each.value["required_pull_request_reviews"], "required_approving_review_count", 0)
    }
  }

  push_restrictions = [
    for actor in each.value["push_restrictions"] : data.github_user.actor[actor]["node_id"]
  ]

  allows_deletions    = each.value["allows_deletions"]
  allows_force_pushes = each.value["allows_force_pushes"]
}