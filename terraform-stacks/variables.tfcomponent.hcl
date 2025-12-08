# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

variable "github_token" {
  description = "GitHub token for API access"
  type        = string
  ephemeral   = true  # Not persisted in state
}

variable "repos" {
  description = "List of repository names to manage"
  type        = set(string)
}

variable "language" {
  description = "Primary language for this deployment (python, nodejs, go, terraform)"
  type        = string
}

# Repository settings
variable "visibility" {
  description = "Repository visibility"
  type        = string
  default     = "public"
}

variable "default_branch" {
  description = "Default branch name"
  type        = string
  default     = "main"
}

# Features
variable "enable_issues" {
  description = "Enable GitHub Issues"
  type        = bool
  default     = true
}

variable "enable_projects" {
  description = "Enable GitHub Projects"
  type        = bool
  default     = false
}

variable "enable_wiki" {
  description = "Enable GitHub Wiki"
  type        = bool
  default     = false
}

variable "enable_discussions" {
  description = "Enable GitHub Discussions"
  type        = bool
  default     = false
}

variable "enable_pages" {
  description = "Enable GitHub Pages"
  type        = bool
  default     = true
}

# Merge settings
variable "allow_squash_merge" {
  description = "Allow squash merging"
  type        = bool
  default     = true
}

variable "allow_merge_commit" {
  description = "Allow merge commits"
  type        = bool
  default     = false
}

variable "allow_rebase_merge" {
  description = "Allow rebase merging"
  type        = bool
  default     = false
}

variable "delete_branch_on_merge" {
  description = "Delete branch after merge"
  type        = bool
  default     = true
}

variable "allow_auto_merge" {
  description = "Allow auto-merge"
  type        = bool
  default     = false
}

# Security
variable "enable_secret_scanning" {
  description = "Enable secret scanning"
  type        = bool
  default     = true
}

variable "enable_push_protection" {
  description = "Enable secret scanning push protection"
  type        = bool
  default     = true
}

variable "enable_dependabot" {
  description = "Enable Dependabot security updates"
  type        = bool
  default     = true
}

# Branch protection
variable "required_approvals" {
  description = "Number of required approving reviews"
  type        = number
  default     = 0
}

variable "dismiss_stale_reviews" {
  description = "Dismiss stale reviews on new commits"
  type        = bool
  default     = false
}

variable "require_code_owner_reviews" {
  description = "Require code owner reviews"
  type        = bool
  default     = false
}

variable "require_last_push_approval" {
  description = "Require approval from non-pusher"
  type        = bool
  default     = false
}

variable "require_linear_history" {
  description = "Require linear history"
  type        = bool
  default     = false
}

variable "require_signed_commits" {
  description = "Require signed commits"
  type        = bool
  default     = false
}

variable "allow_force_pushes" {
  description = "Allow force pushes"
  type        = bool
  default     = false
}

variable "allow_deletions" {
  description = "Allow branch deletions"
  type        = bool
  default     = false
}

variable "required_status_checks" {
  description = "Required status check contexts"
  type        = list(string)
  default     = []
}

variable "strict_status_checks" {
  description = "Require branch to be up to date"
  type        = bool
  default     = false
}
