# Synced Files Module
# Manages repository files via github_repository_file
# Replaces the GitHub Actions file sync workflow

variable "repository" {
  type        = string
  description = "Repository name"
}

variable "branch" {
  type        = string
  default     = "main"
  description = "Target branch for file commits"
}

variable "language" {
  type        = string
  description = "Language type: python, nodejs, go, terraform"
  validation {
    condition     = contains(["python", "nodejs", "go", "terraform"], var.language)
    error_message = "Language must be one of: python, nodejs, go, terraform"
  }
}

variable "commit_author" {
  type    = string
  default = "jbcom-control-center[bot]"
}

variable "commit_email" {
  type    = string
  default = "jbcom-control-center[bot]@users.noreply.github.com"
}

locals {
  # Always-sync files (all repos get these)
  always_sync_files = {
    ".cursor/rules/00-fundamentals.mdc" = file("${path.module}/../../../repository-files/always-sync/.cursor/rules/00-fundamentals.mdc")
    ".cursor/rules/01-pr-workflow.mdc"  = file("${path.module}/../../../repository-files/always-sync/.cursor/rules/01-pr-workflow.mdc")
    ".cursor/rules/02-memory-bank.mdc"  = file("${path.module}/../../../repository-files/always-sync/.cursor/rules/02-memory-bank.mdc")
    ".cursor/rules/ci.mdc"              = file("${path.module}/../../../repository-files/always-sync/.cursor/rules/ci.mdc")
    ".cursor/rules/releases.mdc"        = file("${path.module}/../../../repository-files/always-sync/.cursor/rules/releases.mdc")
    ".github/workflows/claude-code.yml" = file("${path.module}/../../../repository-files/always-sync/.github/workflows/claude-code.yml")
  }

  # Language-specific files
  language_files = {
    python = {
      ".cursor/rules/python.mdc" = file("${path.module}/../../../repository-files/python/.cursor/rules/python.mdc")
    }
    nodejs = {
      ".cursor/rules/typescript.mdc" = file("${path.module}/../../../repository-files/nodejs/.cursor/rules/typescript.mdc")
    }
    go = {
      ".cursor/rules/go.mdc" = file("${path.module}/../../../repository-files/go/.cursor/rules/go.mdc")
    }
    terraform = {
      ".cursor/rules/terraform.mdc" = file("${path.module}/../../../repository-files/terraform/.cursor/rules/terraform.mdc")
    }
  }

  # Merge always-sync + language-specific
  all_files = merge(local.always_sync_files, local.language_files[var.language])
}

# Manage each file in the repository
resource "github_repository_file" "synced" {
  for_each = local.all_files

  repository          = var.repository
  branch              = var.branch
  file                = each.key
  content             = each.value
  commit_message      = "chore: sync ${each.key} from jbcom-control-center"
  commit_author       = var.commit_author
  commit_email        = var.commit_email
  overwrite_on_create = true

  lifecycle {
    ignore_changes = [commit_message]
  }
}

output "synced_files" {
  value = keys(local.all_files)
}
