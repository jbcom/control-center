# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

variable "name" {
  description = "Repository name"
  type        = string
}

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
  type    = bool
  default = true
}

variable "enable_projects" {
  type    = bool
  default = false
}

variable "enable_wiki" {
  type    = bool
  default = false
}

variable "enable_discussions" {
  type    = bool
  default = false
}

variable "enable_pages" {
  type    = bool
  default = true
}

# Merge settings
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

# Security
variable "enable_secret_scanning" {
  type    = bool
  default = true
}

variable "enable_push_protection" {
  type    = bool
  default = true
}

variable "enable_dependabot" {
  type    = bool
  default = true
}

# Branch protection
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

variable "require_linear_history" {
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

variable "required_status_checks" {
  type    = list(string)
  default = []
}

variable "strict_status_checks" {
  type    = bool
  default = false
}
