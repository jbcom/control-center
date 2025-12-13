# TFE Workspace Provisioning Module
# Pre-provisions Terraform Cloud workspaces for all managed repositories
# Must be applied BEFORE running individual repository stacks
#
# Authentication:
#   Uses TF_API_TOKEN environment variable for BOTH:
#   - Terraform Cloud backend authentication
#   - TFE provider API calls
#   This is the same token - no separate configuration needed.
#
# Usage:
#   export TF_API_TOKEN="your-tfc-token"
#   terragrunt init
#   terragrunt apply

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.58"
    }
  }
}

variable "organization" {
  type        = string
  description = "Terraform Cloud organization name"
  default     = "jbcom"
}

variable "github_owner" {
  type        = string
  description = "GitHub owner (user or org) for VCS integration"
  default     = "jbdevprimary"
}

variable "github_oauth_token_id" {
  type        = string
  description = "OAuth token ID for GitHub VCS provider in TFC"
  default     = ""
}

variable "repositories" {
  type = map(object({
    language    = string
    description = optional(string, "")
    tags        = optional(list(string), [])
  }))
  description = "Map of repository names to their configuration"
}

variable "default_execution_mode" {
  type        = string
  description = "Default execution mode for workspaces"
  default     = "remote"
  validation {
    condition     = contains(["remote", "local", "agent"], var.default_execution_mode)
    error_message = "Execution mode must be one of: remote, local, agent"
  }
}

variable "auto_apply" {
  type        = bool
  description = "Whether to auto-apply successful plans"
  default     = false
}

variable "allow_destroy_plan" {
  type        = bool
  description = "Whether to allow destroy plans"
  default     = true
}

variable "global_remote_state" {
  type        = bool
  description = "Allow all workspaces to access each other's state"
  default     = true
}

# Data source for the organization
data "tfe_organization" "this" {
  name = var.organization
}

# Create a workspace for each repository
resource "tfe_workspace" "repo" {
  for_each = var.repositories

  name         = "jbcom-repo-${each.key}"
  organization = data.tfe_organization.this.name
  description  = coalesce(each.value.description, "Repository management for ${each.key}")

  # Execution settings
  execution_mode = var.default_execution_mode
  auto_apply     = var.auto_apply

  # Working directory - each repo has its own terragrunt directory
  working_directory = "terragrunt-stacks/${each.value.language}/${each.key}"

  # Allow destroy operations
  allow_destroy_plan = var.allow_destroy_plan

  # Enable global remote state sharing
  global_remote_state = var.global_remote_state

  # VCS integration (optional - can be CLI-driven instead)
  dynamic "vcs_repo" {
    for_each = var.github_oauth_token_id != "" ? [1] : []
    content {
      identifier     = "${var.github_owner}/jbcom-control-center"
      oauth_token_id = var.github_oauth_token_id
      branch         = "main"
    }
  }

  # Tags for organization
  tag_names = concat(
    ["managed", "repository", each.value.language],
    each.value.tags
  )

  lifecycle {
    prevent_destroy = true
  }
}

# Create workspace variables for GitHub token (required for all workspaces)
resource "tfe_variable" "github_token" {
  for_each = var.repositories

  key          = "GITHUB_TOKEN"
  value        = "" # Set via TFC UI or API - never in code
  category     = "env"
  sensitive    = true
  workspace_id = tfe_workspace.repo[each.key].id
  description  = "GitHub token for repository operations"

  lifecycle {
    ignore_changes = [value] # Never overwrite the actual token value
  }
}

# Outputs
output "workspace_ids" {
  value = { for k, v in tfe_workspace.repo : k => v.id }
  description = "Map of repository names to workspace IDs"
}

output "workspace_names" {
  value = { for k, v in tfe_workspace.repo : k => v.name }
  description = "Map of repository names to workspace names"
}

output "workspace_urls" {
  value = {
    for k, v in tfe_workspace.repo : k => "https://app.terraform.io/app/${var.organization}/workspaces/${v.name}"
  }
  description = "Map of repository names to workspace URLs"
}
