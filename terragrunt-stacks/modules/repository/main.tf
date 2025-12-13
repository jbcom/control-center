# Repository module - manages a single GitHub repository
# Also syncs standard files (Cursor rules, workflows) via github_repository_file

# =============================================================================
# REQUIRED VARIABLES - These differ per repository
# =============================================================================

variable "name" {
  type = string
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
# OPTIONAL VARIABLES - Repository features that may differ
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
  default = false
}

variable "has_pages" {
  type    = bool
  default = true
}

variable "default_branch" {
  type    = string
  default = "main"
}

variable "feature_branch_patterns" {
  type        = list(string)
  default     = []
  description = "List of branch patterns for feature branches (e.g., ['feature/*', 'bugfix/*'])"
}

# =============================================================================
# OPTIONAL VARIABLES - Branch protection settings
# =============================================================================

variable "require_signed_commits" {
  type        = bool
  default     = false
  description = "Require signed commits on the default branch"
}

variable "allow_force_pushes" {
  type        = bool
  default     = false
  description = "Allow force pushes to the default branch"
}

variable "allow_deletions" {
  type        = bool
  default     = false
  description = "Allow deletion of the default branch"
}

variable "lock_branch" {
  type        = bool
  default     = false
  description = "Lock the default branch (prevent any pushes)"
}

variable "required_linear_history" {
  type        = bool
  default     = false
  description = "Require linear history on the default branch"
}

variable "required_status_checks_strict" {
  type        = bool
  default     = false
  description = "Require branches to be up to date before merging"
}

variable "required_status_checks_contexts" {
  type        = list(string)
  default     = []
  description = "List of required status check contexts"
}

# =============================================================================
# SECRETS - Passed from CI via TF_VAR_* environment variables
# =============================================================================

variable "ci_github_token" {
  type        = string
  sensitive   = true
  description = "CI GitHub token for workflows"
  default     = ""
}

variable "pypi_token" {
  type        = string
  sensitive   = true
  description = "PyPI token for package publishing"
  default     = ""
}

variable "npm_token" {
  type        = string
  sensitive   = true
  description = "NPM token for package publishing"
  default     = ""
}

variable "dockerhub_username" {
  type        = string
  sensitive   = true
  description = "DockerHub username"
  default     = ""
}

variable "dockerhub_token" {
  type        = string
  sensitive   = true
  description = "DockerHub token"
  default     = ""
}

variable "anthropic_api_key" {
  type        = string
  sensitive   = true
  description = "Anthropic API key for AI features"
  default     = ""
}

variable "ollama_api_key" {
  type        = string
  sensitive   = true
  description = "Ollama Cloud API key for AI triage"
  default     = ""
}

# =============================================================================
# LOCALS - Standard settings, no need for variables
# =============================================================================

locals {
  repo_files = "${path.root}/../../../repository-files"

  # Repository settings - standardized across all repos
  repo_settings = {
    allow_squash_merge     = true
    allow_merge_commit     = false
    allow_rebase_merge     = false
    delete_branch_on_merge = true
    allow_auto_merge       = false
    vulnerability_alerts   = true
  }

  # Main branch protection - uses variables for configurable settings
  main_branch_protection = {
    required_approvals              = 0
    dismiss_stale_reviews           = false
    require_code_owner_reviews      = false
    require_last_push_approval      = false
    require_conversation_resolution = true
    required_linear_history         = var.required_linear_history
    require_signed_commits          = var.require_signed_commits
    allow_force_pushes              = var.allow_force_pushes
    allow_deletions                 = var.allow_deletions
    lock_branch                     = var.lock_branch
  }

  # Feature branch protection - lighter than main
  feature_branch_protection = {
    allow_deletions                 = true
    allow_force_pushes              = false
    require_conversation_resolution = false
  }

  # File sync paths
  always_sync_files = {
    for file in setunion(
      fileset("${local.repo_files}/always-sync", "**/*"),
      fileset("${local.repo_files}/always-sync", "**/.[!.]*")
    ) : file => "${local.repo_files}/always-sync/${file}"
  }

  language_files = {
    for file in setunion(
      fileset("${local.repo_files}/${var.language}", "**/*"),
      fileset("${local.repo_files}/${var.language}", "**/.[!.]*")
    ) : file => "${local.repo_files}/${var.language}/${file}"
  }

  initial_only_files = {
    for file in setunion(
      fileset("${local.repo_files}/initial-only", "**/*"),
      fileset("${local.repo_files}/initial-only", "**/.[!.]*")
    ) : file => "${local.repo_files}/initial-only/${file}"
  }

  all_synced_files = merge(local.always_sync_files, local.language_files)
}

# =============================================================================
# REPOSITORY
# =============================================================================

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
# BRANCH PROTECTION RULESETS
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
    deletion                = !local.main_branch_protection.allow_deletions
    non_fast_forward        = !local.main_branch_protection.allow_force_pushes
    required_linear_history = local.main_branch_protection.required_linear_history
    required_signatures     = local.main_branch_protection.require_signed_commits
    update                  = local.main_branch_protection.lock_branch

    pull_request {
      required_approving_review_count   = local.main_branch_protection.required_approvals
      dismiss_stale_reviews_on_push     = local.main_branch_protection.dismiss_stale_reviews
      require_code_owner_review         = local.main_branch_protection.require_code_owner_reviews
      require_last_push_approval        = local.main_branch_protection.require_last_push_approval
      required_review_thread_resolution = local.main_branch_protection.require_conversation_resolution
    }

    dynamic "required_status_checks" {
      for_each = length(var.required_status_checks_contexts) > 0 ? [1] : []
      content {
        strict_required_status_checks_policy = var.required_status_checks_strict
        dynamic "required_check" {
          for_each = var.required_status_checks_contexts
          content {
            context = required_check.value
          }
        }
      }
    }
  }

  bypass_actors {
    actor_id    = 5 # Repository admin role
    actor_type  = "RepositoryRole"
    bypass_mode = "always"
  }
}

resource "github_repository_ruleset" "feature" {
  count = length(var.feature_branch_patterns) > 0 ? 1 : 0

  name        = "Feature"
  repository  = github_repository.this.name
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = var.feature_branch_patterns
      exclude = []
    }
  }

  rules {
    deletion         = !local.feature_branch_protection.allow_deletions
    non_fast_forward = !local.feature_branch_protection.allow_force_pushes
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
# SECRETS
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
  value = github_repository.this.html_url
}

output "id" {
  value = github_repository.this.id
}

output "synced_files" {
  value = keys(local.all_synced_files)
}

output "initial_files" {
  value = keys(local.initial_only_files)
}

output "main_ruleset" {
  value = {
    name        = github_repository_ruleset.main.name
    enforcement = github_repository_ruleset.main.enforcement
  }
}

output "feature_branch_patterns" {
  value = var.feature_branch_patterns
}

output "feature_ruleset" {
  value = length(var.feature_branch_patterns) > 0 ? {
    name        = github_repository_ruleset.feature[0].name
    enforcement = github_repository_ruleset.feature[0].enforcement
    patterns    = var.feature_branch_patterns
  } : null
}
