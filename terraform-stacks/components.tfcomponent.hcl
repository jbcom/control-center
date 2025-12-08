# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

# Repository component - manages a set of repositories with shared configuration
component "repositories" {
  source   = "./repository"
  for_each = var.repos

  inputs = {
    name = each.value

    # Settings from deployment
    visibility             = var.visibility
    default_branch         = var.default_branch
    enable_issues          = var.enable_issues
    enable_projects        = var.enable_projects
    enable_wiki            = var.enable_wiki
    enable_discussions     = var.enable_discussions
    enable_pages           = var.enable_pages
    allow_squash_merge     = var.allow_squash_merge
    allow_merge_commit     = var.allow_merge_commit
    allow_rebase_merge     = var.allow_rebase_merge
    delete_branch_on_merge = var.delete_branch_on_merge
    allow_auto_merge       = var.allow_auto_merge

    # Security
    enable_secret_scanning = var.enable_secret_scanning
    enable_push_protection = var.enable_push_protection
    enable_dependabot      = var.enable_dependabot

    # Branch protection
    required_approvals         = var.required_approvals
    dismiss_stale_reviews      = var.dismiss_stale_reviews
    require_code_owner_reviews = var.require_code_owner_reviews
    require_last_push_approval = var.require_last_push_approval
    require_linear_history     = var.require_linear_history
    require_signed_commits     = var.require_signed_commits
    allow_force_pushes         = var.allow_force_pushes
    allow_deletions            = var.allow_deletions
    required_status_checks     = var.required_status_checks
    strict_status_checks       = var.strict_status_checks
  }

  providers = {
    github = provider.github.jbcom
  }
}
