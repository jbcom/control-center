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

variable "sync_files" {
  type        = bool
  default     = true
  description = "Whether to sync standard files (Cursor rules, workflows)"
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

  # Status checks - configurable per repository
  # Default: no required checks (repos can customize via terragrunt inputs)
  required_status_checks {
    strict   = var.required_status_checks_strict
    contexts = var.required_status_checks_contexts
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

# =============================================================================
# SYNCED FILES - Cursor rules and workflows managed via Terraform
# =============================================================================

locals {
  # Absolute path to repository-files at workspace root
  repo_files = "/workspace/repository-files"

  # Always-sync files (overwrite every time)
  always_sync_files = var.sync_files ? {
    ".cursor/rules/00-fundamentals.mdc" = "${local.repo_files}/always-sync/.cursor/rules/00-fundamentals.mdc"
    ".cursor/rules/01-pr-workflow.mdc"  = "${local.repo_files}/always-sync/.cursor/rules/01-pr-workflow.mdc"
    ".cursor/rules/02-memory-bank.mdc"  = "${local.repo_files}/always-sync/.cursor/rules/02-memory-bank.mdc"
    ".cursor/rules/ci.mdc"              = "${local.repo_files}/always-sync/.cursor/rules/ci.mdc"
    ".cursor/rules/releases.mdc"        = "${local.repo_files}/always-sync/.cursor/rules/releases.mdc"
    ".github/workflows/claude-code.yml" = "${local.repo_files}/always-sync/.github/workflows/claude-code.yml"
  } : {}

  # Language-specific files (always sync)
  language_file_paths = {
    python    = "${local.repo_files}/python/.cursor/rules/python.mdc"
    nodejs    = "${local.repo_files}/nodejs/.cursor/rules/typescript.mdc"
    go        = "${local.repo_files}/go/.cursor/rules/go.mdc"
    terraform = "${local.repo_files}/terraform/.cursor/rules/terraform.mdc"
  }

  language_file_dest = {
    python    = ".cursor/rules/python.mdc"
    nodejs    = ".cursor/rules/typescript.mdc"
    go        = ".cursor/rules/go.mdc"
    terraform = ".cursor/rules/terraform.mdc"
  }

  language_files = var.sync_files ? {
    (local.language_file_dest[var.language]) = local.language_file_paths[var.language]
  } : {}

  # Initial-only files (create once, repos customize after)
  initial_only_files = var.sync_files ? {
    ".cursor/environment.json"             = "${local.repo_files}/initial-only/.cursor/environment.json"
    ".github/workflows/docs.yml"           = "${local.repo_files}/initial-only/.github/workflows/docs.yml"
    "docs/Makefile"                        = "${local.repo_files}/initial-only/docs/Makefile"
    "docs/conf.py"                         = "${local.repo_files}/initial-only/docs/conf.py"
    "docs/index.rst"                       = "${local.repo_files}/initial-only/docs/index.rst"
    "docs/.nojekyll"                       = "${local.repo_files}/initial-only/docs/.nojekyll"
    "docs/_static/custom.css"              = "${local.repo_files}/initial-only/docs/_static/custom.css"
    "docs/_templates/.gitkeep"             = "${local.repo_files}/initial-only/docs/_templates/.gitkeep"
    "docs/api/index.rst"                   = "${local.repo_files}/initial-only/docs/api/index.rst"
    "docs/api/modules.rst"                 = "${local.repo_files}/initial-only/docs/api/modules.rst"
    "docs/development/contributing.md"     = "${local.repo_files}/initial-only/docs/development/contributing.md"
    "docs/getting-started/installation.md" = "${local.repo_files}/initial-only/docs/getting-started/installation.md"
    "docs/getting-started/quickstart.md"   = "${local.repo_files}/initial-only/docs/getting-started/quickstart.md"
  } : {}

  # All always-sync files
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
