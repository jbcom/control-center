# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

# Repository settings
resource "github_repository" "this" {
  name = var.name

  visibility = var.visibility

  # Features
  has_issues      = var.enable_issues
  has_projects    = var.enable_projects
  has_wiki        = var.enable_wiki
  has_discussions = var.enable_discussions

  # Merge settings
  allow_squash_merge     = var.allow_squash_merge
  allow_merge_commit     = var.allow_merge_commit
  allow_rebase_merge     = var.allow_rebase_merge
  delete_branch_on_merge = var.delete_branch_on_merge
  allow_auto_merge       = var.allow_auto_merge

  # Security
  vulnerability_alerts = var.enable_dependabot

  lifecycle {
    prevent_destroy = true
  }
}

# Branch protection
resource "github_branch_protection" "main" {
  repository_id = github_repository.this.node_id
  pattern       = var.default_branch

  required_pull_request_reviews {
    dismiss_stale_reviews           = var.dismiss_stale_reviews
    require_code_owner_reviews      = var.require_code_owner_reviews
    required_approving_review_count = var.required_approvals
    require_last_push_approval      = var.require_last_push_approval
  }

  required_status_checks {
    strict   = var.strict_status_checks
    contexts = var.required_status_checks
  }

  require_linear_history = var.require_linear_history
  require_signed_commits = var.require_signed_commits
  allows_force_pushes    = var.allow_force_pushes
  allows_deletions       = var.allow_deletions
}

# Security settings
resource "github_repository_security_and_analysis" "this" {
  repository = github_repository.this.name

  secret_scanning {
    status = var.enable_secret_scanning ? "enabled" : "disabled"
  }

  secret_scanning_push_protection {
    status = var.enable_push_protection ? "enabled" : "disabled"
  }
}

# GitHub Pages (conditional)
resource "github_repository_pages" "this" {
  count = var.enable_pages ? 1 : 0

  repository = github_repository.this.name

  source {
    branch = var.default_branch
  }

  build_type = "workflow"

  lifecycle {
    ignore_changes = [cname]
  }
}
