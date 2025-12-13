# Repository module - manages a single GitHub repository
# Modern, modular, DRY design using github_repository_ruleset (not deprecated branch_protection)
#
# Features:
# - Repository settings (merge strategies, features)
# - Branch protection via rulesets (modern API)
# - File synchronization from control center
# - Secrets management via for_each

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

# =============================================================================
# OPTIONAL VARIABLES - Branch protection settings
# =============================================================================

variable "feature_branch_patterns" {
  type        = list(string)
  default     = []
  description = "Branch patterns WITHOUT refs/heads/ prefix (e.g., ['feature/*', 'bugfix/*'])"
}

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
# SECRETS - Passed via TF_VAR_* environment variables, managed via for_each
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

  # Repository settings - standardized across all repos
  repo_settings = {
    allow_squash_merge     = true
    allow_merge_commit     = false
    allow_rebase_merge     = false
    delete_branch_on_merge = true
    allow_auto_merge       = false
    vulnerability_alerts   = true
  }

  # Main branch protection settings
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
    allow_deletions    = true
    allow_force_pushes = false
  }

  # Convert branch patterns to refs/heads/ format for rulesets
  # GitHub rulesets require the refs/heads/ prefix for branch patterns
  feature_branch_refs = [
    for pattern in var.feature_branch_patterns :
    "refs/heads/${pattern}"
  ]

  # DRY secrets map - only include non-empty secrets
  secrets_map = {
    CI_GITHUB_TOKEN    = var.ci_github_token
    PYPI_TOKEN         = var.pypi_token
    NPM_TOKEN          = var.npm_token
    DOCKERHUB_USERNAME = var.dockerhub_username
    DOCKERHUB_TOKEN    = var.dockerhub_token
    ANTHROPIC_API_KEY  = var.anthropic_api_key
    OLLAMA_API_KEY     = var.ollama_api_key
  }

  # Filter to only non-empty secrets
  secrets_to_sync = {
    for name, value in local.secrets_map :
    name => value if value != ""
  }

  # File sync - exclude directories, binary files, and special files
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
# BRANCH PROTECTION RULESETS (Modern API - replaces deprecated branch_protection)
# =============================================================================

resource "github_repository_ruleset" "main" {
  name        = "main-branch-protection"
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

# Feature branch protection ruleset - only created if patterns are provided
resource "github_repository_ruleset" "feature" {
  count = length(var.feature_branch_patterns) > 0 ? 1 : 0

  name        = "feature-branch-protection"
  repository  = github_repository.this.name
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      # Use refs/heads/ prefix for branch patterns as required by GitHub API
      include = local.feature_branch_refs
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
# SECRETS - DRY implementation using for_each
# =============================================================================

resource "github_actions_secret" "managed" {
  for_each = local.secrets_to_sync

  repository      = github_repository.this.name
  secret_name     = each.key
  plaintext_value = each.value
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

output "feature_ruleset" {
  value = length(var.feature_branch_patterns) > 0 ? {
    name        = github_repository_ruleset.feature[0].name
    enforcement = github_repository_ruleset.feature[0].enforcement
    patterns    = local.feature_branch_refs
  } : null
  description = "Feature branch protection ruleset"
}

output "secrets_synced" {
  value       = keys(local.secrets_to_sync)
  description = "List of secrets synced to repository"
  sensitive   = false
}
