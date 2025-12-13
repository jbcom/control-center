# Repository module - manages a single GitHub repository
# Also syncs standard files (Cursor rules, workflows) via github_repository_file

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
  default = true # All repos use GitHub Actions Pages
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

variable "required_status_checks_strict" {
  type        = bool
  default     = false
  description = "Require branches to be up to date before merging"
}

variable "required_status_checks_contexts" {
  type        = list(string)
  default     = []
  description = "List of required status check contexts (e.g., ['ci/build', 'ci/test'])"
}

variable "require_conversation_resolution" {
  type        = bool
  default     = true
  description = "Require all PR conversations to be resolved before merging"
}

variable "lock_branch" {
  type        = bool
  default     = false
  description = "Lock branch to make it read-only (prevents all pushes)"
}

# Feature branch protection configuration
variable "feature_branch_patterns" {
  type        = list(string)
  default     = []
  description = "List of branch patterns for feature branches (e.g., ['feature/*', 'bugfix/*'])"
}

variable "feature_required_approvals" {
  type        = number
  default     = 0
  description = "Number of required approvals for feature branches"
}

variable "feature_required_status_checks_contexts" {
  type        = list(string)
  default     = []
  description = "List of required status check contexts for feature branches"
}

variable "feature_allow_force_pushes" {
  type        = bool
  default     = false
  description = "Allow force pushes to feature branches"
}

variable "feature_allow_deletions" {
  type        = bool
  default     = true
  description = "Allow deletion of feature branches (typically true for cleanup)"
}

variable "feature_require_conversation_resolution" {
  type        = bool
  default     = false
  description = "Require conversation resolution on feature branches (typically false for lighter protection)"
}

# Secrets to sync to the repository
# These are passed as TF_VAR_* environment variables from the workflow
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

  # Security configuration - secret scanning and push protection
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

# Main branch ruleset - matches strata configuration
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
    required_linear_history = true

    pull_request {
      required_approving_review_count   = var.required_approvals
      dismiss_stale_reviews_on_push     = var.dismiss_stale_reviews
      require_code_owner_review         = var.require_code_owner_reviews
      require_last_push_approval        = var.require_last_push_approval
      required_review_thread_resolution = var.require_conversation_resolution
    }
  }

  bypass_actors {
    actor_id    = 5 # Repository admin role
    actor_type  = "RepositoryRole"
    bypass_mode = "always"
  }
}

output "url" {
  value = github_repository.this.html_url
}

output "id" {
  value = github_repository.this.id
}

# =============================================================================
# SYNCED FILES - Cursor rules and workflows managed via Terraform
# =============================================================================

locals {
  repo_files = "${path.root}/../../../repository-files"

  # Always-sync: **/* for regular files, **/.[!.]* for dotfiles
  always_sync_files = {
    for file in setunion(
      fileset("${local.repo_files}/always-sync", "**/*"),
      fileset("${local.repo_files}/always-sync", "**/.[!.]*")
    ) : file => "${local.repo_files}/always-sync/${file}"
  }

  # Language-specific
  language_files = {
    for file in setunion(
      fileset("${local.repo_files}/${var.language}", "**/*"),
      fileset("${local.repo_files}/${var.language}", "**/.[!.]*")
    ) : file => "${local.repo_files}/${var.language}/${file}"
  }

  # Initial-only
  initial_only_files = {
    for file in setunion(
      fileset("${local.repo_files}/initial-only", "**/*"),
      fileset("${local.repo_files}/initial-only", "**/.[!.]*")
    ) : file => "${local.repo_files}/initial-only/${file}"
  }

  all_synced_files = merge(local.always_sync_files, local.language_files)
}

# Always-sync files - overwrite on every apply
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

# Initial-only files - create once, repos customize after
resource "github_repository_file" "initial" {
  for_each = local.initial_only_files

  repository          = github_repository.this.name
  branch              = var.default_branch
  file                = each.key
  content             = file(each.value)
  commit_message      = "chore: initial ${each.key} from jbcom-control-center"
  commit_author       = "jbcom-control-center[bot]"
  commit_email        = "jbcom-control-center[bot]@users.noreply.github.com"
  overwrite_on_create = true # Allow import of existing files

  lifecycle {
    ignore_changes = [content, commit_message, commit_author, commit_email] # Never update after creation
  }
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
  description = "Main branch ruleset settings"
}

output "feature_branch_patterns" {
  value       = var.feature_branch_patterns
  description = "Protected feature branch patterns"
}

# GitHub Actions Secrets
# Sync secrets to the repository from environment variables

# Individual secret resources - only created when the variable is non-empty
# We use separate resources to avoid the "sensitive value in for_each" error

resource "github_actions_secret" "ci_github_token" {
  count = var.ci_github_token != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "CI_GITHUB_TOKEN"
  plaintext_value = var.ci_github_token
}

resource "github_actions_secret" "pypi_token" {
  count = var.pypi_token != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "PYPI_TOKEN"
  plaintext_value = var.pypi_token
}

resource "github_actions_secret" "npm_token" {
  count = var.npm_token != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "NPM_TOKEN"
  plaintext_value = var.npm_token
}

resource "github_actions_secret" "dockerhub_username" {
  count = var.dockerhub_username != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "DOCKERHUB_USERNAME"
  plaintext_value = var.dockerhub_username
}

resource "github_actions_secret" "dockerhub_token" {
  count = var.dockerhub_token != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "DOCKERHUB_TOKEN"
  plaintext_value = var.dockerhub_token
}

resource "github_actions_secret" "anthropic_api_key" {
  count = var.anthropic_api_key != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "ANTHROPIC_API_KEY"
  plaintext_value = var.anthropic_api_key
}

resource "github_actions_secret" "ollama_api_key" {
  count = var.ollama_api_key != "" ? 1 : 0

  repository      = github_repository.this.name
  secret_name     = "OLLAMA_API_KEY"
  plaintext_value = var.ollama_api_key
}
