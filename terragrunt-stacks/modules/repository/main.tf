# Repository module - manages a single GitHub repository
# Based on Strata repository patterns (modern, clean, no deprecated resources)
#
# Uses github_repository_ruleset (modern API) instead of deprecated github_branch_protection

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    github = {
      source  = "integrations/github"
      version = ">= 6.0"
    }
  }
}

# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

variable "name" {
  type        = string
  description = "Repository name"
}

variable "language" {
  type        = string
  description = "Language type: python, nodejs, go, terraform"
  validation {
    condition     = contains(["python", "nodejs", "go", "terraform"], var.language)
    error_message = "Language must be one of: python, nodejs, go, terraform"
  }
}

# =============================================================================
# OPTIONAL VARIABLES - Repository features
# =============================================================================

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
  default = true
}

variable "has_pages" {
  type    = bool
  default = true
}

variable "default_branch" {
  type    = string
  default = "main"
}

# =============================================================================
# OPTIONAL VARIABLES - Main branch protection settings
# =============================================================================

variable "required_linear_history" {
  type        = bool
  default     = true
  description = "Require linear history on the default branch"
}

variable "required_approving_review_count" {
  type        = number
  default     = 0
  description = "Number of required approving reviews"
}

variable "require_conversation_resolution" {
  type        = bool
  default     = true
  description = "Require conversation resolution before merging"
}

# =============================================================================
# SECRETS - Passed via TF_VAR_* environment variables
# =============================================================================

variable "ci_github_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "pypi_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "npm_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "dockerhub_username" {
  type      = string
  sensitive = true
  default   = ""
}

variable "dockerhub_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "ollama_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

# =============================================================================
# LOCALS
# =============================================================================

locals {
  repo_files = "${path.root}/../../../repository-files"

  # Repository settings - standardized across all repos (matching Strata)
  repo_settings = {
    allow_squash_merge     = true
    allow_merge_commit     = false
    allow_rebase_merge     = false
    delete_branch_on_merge = true
    allow_auto_merge       = false
    vulnerability_alerts   = true
  }

  # File sync - exclude binary files
  always_sync_files = {
    for file in setunion(
      fileset("${local.repo_files}/always-sync", "**/*"),
      fileset("${local.repo_files}/always-sync", "**/.[!.]*")
    ) : file => "${local.repo_files}/always-sync/${file}"
    if !can(regex("\\.(png|jpg|jpeg|gif|ico|woff|woff2|ttf|eot|pdf|zip|tar|gz)$", file))
  }

  language_files = {
    for file in setunion(
      fileset("${local.repo_files}/${var.language}", "**/*"),
      fileset("${local.repo_files}/${var.language}", "**/.[!.]*")
    ) : file => "${local.repo_files}/${var.language}/${file}"
    if !can(regex("\\.(png|jpg|jpeg|gif|ico|woff|woff2|ttf|eot|pdf|zip|tar|gz)$", file))
  }

  initial_only_files = {
    for file in setunion(
      fileset("${local.repo_files}/initial-only", "**/*"),
      fileset("${local.repo_files}/initial-only", "**/.[!.]*")
    ) : file => "${local.repo_files}/initial-only/${file}"
    if !can(regex("\\.(png|jpg|jpeg|gif|ico|woff|woff2|ttf|eot|pdf|zip|tar|gz)$", file))
  }

  all_synced_files = merge(local.always_sync_files, local.language_files)
}

# =============================================================================
# REPOSITORY
# =============================================================================

resource "github_repository" "this" {
  name       = var.name
  visibility = var.visibility

  has_issues      = var.has_issues
  has_projects    = var.has_projects
  has_wiki        = var.has_wiki
  has_discussions = var.has_discussions

  allow_squash_merge     = local.repo_settings.allow_squash_merge
  allow_merge_commit     = local.repo_settings.allow_merge_commit
  allow_rebase_merge     = local.repo_settings.allow_rebase_merge
  delete_branch_on_merge = local.repo_settings.delete_branch_on_merge
  allow_auto_merge       = local.repo_settings.allow_auto_merge

  vulnerability_alerts = local.repo_settings.vulnerability_alerts

  security_and_analysis {
    secret_scanning {
      status = "enabled"
    }
    secret_scanning_push_protection {
      status = "enabled"
    }
  }

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [description, homepage_url, topics, template]
  }

  dynamic "pages" {
    for_each = var.has_pages ? [1] : []
    content {
      build_type = "workflow"
    }
  }
}

# =============================================================================
# RULESET: Main Branch Protection (based on Strata)
# =============================================================================

resource "github_repository_ruleset" "main" {
  name        = "Main"
  repository  = github_repository.this.name
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["~DEFAULT_BRANCH"]
      exclude = []
    }
  }

  rules {
    non_fast_forward        = true
    required_linear_history = var.required_linear_history

    pull_request {
      required_approving_review_count   = var.required_approving_review_count
      dismiss_stale_reviews_on_push     = false
      require_code_owner_review         = false
      require_last_push_approval        = false
      required_review_thread_resolution = var.require_conversation_resolution
    }
  }

  bypass_actors {
    actor_id    = 5 # Repository admin role
    actor_type  = "RepositoryRole"
    bypass_mode = "always"
  }
}

# =============================================================================
# SYNCED FILES
# =============================================================================

resource "github_repository_file" "synced" {
  for_each = local.all_synced_files

  repository          = github_repository.this.name
  branch              = var.default_branch
  file                = each.key
  content             = file(each.value)
  commit_message      = "chore: sync ${each.key} from jbcom-control-center"
  commit_author       = "jbcom-control-center[bot]"
  commit_email        = "jbcom-control-center[bot]@users.noreply.github.com"
  overwrite_on_create = true

  lifecycle {
    ignore_changes = [commit_message, commit_author, commit_email]
  }
}

resource "github_repository_file" "initial" {
  for_each = local.initial_only_files

  repository          = github_repository.this.name
  branch              = var.default_branch
  file                = each.key
  content             = file(each.value)
  commit_message      = "chore: initial ${each.key} from jbcom-control-center"
  commit_author       = "jbcom-control-center[bot]"
  commit_email        = "jbcom-control-center[bot]@users.noreply.github.com"
  overwrite_on_create = true

  lifecycle {
    ignore_changes = [content, commit_message, commit_author, commit_email]
  }
}

# =============================================================================
# SECRETS - Individual resources (for_each with sensitive values not allowed)
# =============================================================================

resource "github_actions_secret" "ci_github_token" {
  count           = var.ci_github_token != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "CI_GITHUB_TOKEN"
  plaintext_value = var.ci_github_token
}

resource "github_actions_secret" "pypi_token" {
  count           = var.pypi_token != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "PYPI_TOKEN"
  plaintext_value = var.pypi_token
}

resource "github_actions_secret" "npm_token" {
  count           = var.npm_token != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "NPM_TOKEN"
  plaintext_value = var.npm_token
}

resource "github_actions_secret" "dockerhub_username" {
  count           = var.dockerhub_username != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "DOCKERHUB_USERNAME"
  plaintext_value = var.dockerhub_username
}

resource "github_actions_secret" "dockerhub_token" {
  count           = var.dockerhub_token != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "DOCKERHUB_TOKEN"
  plaintext_value = var.dockerhub_token
}

resource "github_actions_secret" "anthropic_api_key" {
  count           = var.anthropic_api_key != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "ANTHROPIC_API_KEY"
  plaintext_value = var.anthropic_api_key
}

resource "github_actions_secret" "ollama_api_key" {
  count           = var.ollama_api_key != "" ? 1 : 0
  repository      = github_repository.this.name
  secret_name     = "OLLAMA_API_KEY"
  plaintext_value = var.ollama_api_key
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "url" {
  value       = github_repository.this.html_url
  description = "Repository URL"
}

output "id" {
  value       = github_repository.this.id
  description = "Repository ID"
}

output "synced_files" {
  value       = keys(local.all_synced_files)
  description = "List of files synced to repository"
}

output "initial_files" {
  value       = keys(local.initial_only_files)
  description = "List of initial-only files"
}

output "main_ruleset" {
  value = {
    name        = github_repository_ruleset.main.name
    enforcement = github_repository_ruleset.main.enforcement
  }
  description = "Main branch protection ruleset"
}
