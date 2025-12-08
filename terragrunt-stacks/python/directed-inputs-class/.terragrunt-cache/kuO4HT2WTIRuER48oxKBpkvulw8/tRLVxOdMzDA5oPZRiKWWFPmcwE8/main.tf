# Repository module - manages a single GitHub repository

variable "name" {
  type = string
}

variable "visibility" {
  type    = string
  default = "public"
}

variable "has_issues" {
  type    = bool
  default = true
}

variable "has_projects" {
  type    = bool
  default = false
}

variable "has_wiki" {
  type    = bool
  default = false
}

variable "has_discussions" {
  type    = bool
  default = false
}

variable "allow_squash_merge" {
  type    = bool
  default = true
}

variable "allow_merge_commit" {
  type    = bool
  default = false
}

variable "allow_rebase_merge" {
  type    = bool
  default = false
}

variable "delete_branch_on_merge" {
  type    = bool
  default = true
}

variable "allow_auto_merge" {
  type    = bool
  default = false
}

variable "vulnerability_alerts" {
  type    = bool
  default = true
}

variable "default_branch" {
  type    = string
  default = "main"
}

variable "required_approvals" {
  type    = number
  default = 0
}

variable "dismiss_stale_reviews" {
  type    = bool
  default = false
}

variable "require_code_owner_reviews" {
  type    = bool
  default = false
}

variable "require_last_push_approval" {
  type    = bool
  default = false
}

variable "required_linear_history" {
  type    = bool
  default = false
}

variable "require_signed_commits" {
  type    = bool
  default = false
}

variable "allow_force_pushes" {
  type    = bool
  default = false
}

variable "allow_deletions" {
  type    = bool
  default = false
}

# Import existing repository
import {
  to = github_repository.this
  id = var.name
}

resource "github_repository" "this" {
  name       = var.name
  visibility = var.visibility

  has_issues      = var.has_issues
  has_projects    = var.has_projects
  has_wiki        = var.has_wiki
  has_discussions = var.has_discussions

  allow_squash_merge     = var.allow_squash_merge
  allow_merge_commit     = var.allow_merge_commit
  allow_rebase_merge     = var.allow_rebase_merge
  delete_branch_on_merge = var.delete_branch_on_merge
  allow_auto_merge       = var.allow_auto_merge

  vulnerability_alerts = var.vulnerability_alerts

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [description, homepage_url, topics, pages]
  }
}

# Import existing branch protection
import {
  to = github_branch_protection.main
  id = "${var.name}:${var.default_branch}"
}

resource "github_branch_protection" "main" {
  repository_id = github_repository.this.node_id
  pattern       = var.default_branch

  required_pull_request_reviews {
    dismiss_stale_reviews           = var.dismiss_stale_reviews
    require_code_owner_reviews      = var.require_code_owner_reviews
    required_approving_review_count = var.required_approvals
    require_last_push_approval      = var.require_last_push_approval
  }

  required_linear_history = var.required_linear_history
  require_signed_commits  = var.require_signed_commits
  allows_force_pushes     = var.allow_force_pushes
  allows_deletions        = var.allow_deletions
}

output "url" {
  value = github_repository.this.html_url
}

output "id" {
  value = github_repository.this.id
}
