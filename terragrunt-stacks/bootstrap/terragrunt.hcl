# Bootstrap stack - provisions TFE workspaces for all repositories
# Run this FIRST before any individual repository stacks
#
# Usage:
#   cd terragrunt-stacks/bootstrap
#   terragrunt init
#   terragrunt plan
#   terragrunt apply
#
# NOTE: This stack does NOT include the root config because it needs
# completely different provider (TFE instead of GitHub) and backend settings.
# This avoids duplicate generate block names when running terragrunt run-all.

terraform {
  source = "../modules/tfe-workspaces"
}

# Configure backend - bootstrap uses its own workspace
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  cloud {
    organization = "jbcom"
    
    workspaces {
      name = "jbcom-bootstrap"
    }
  }
}
EOF
}

# Configure provider - bootstrap needs TFE provider, not GitHub
# NOTE: TF_API_TOKEN is used for BOTH backend auth AND TFE provider auth
# The TFE provider automatically uses TFE_TOKEN or TF_API_TOKEN
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.58"
    }
  }
}

# TFE provider automatically uses TF_API_TOKEN (same token as backend auth)
# No separate configuration needed - single token for everything
provider "tfe" {}
EOF
}

locals {
  # Import repo lists from root config
  root_config = read_terragrunt_config(find_in_parent_folders())
  
  # Build repository map with language info
  python_repos = { for repo in local.root_config.locals.python_repos : repo => {
    language = "python"
    tags     = ["python", "pypi"]
  }}
  
  nodejs_repos = { for repo in local.root_config.locals.nodejs_repos : repo => {
    language = "nodejs"
    tags     = ["nodejs", "npm"]
  }}
  
  go_repos = { for repo in local.root_config.locals.go_repos : repo => {
    language = "go"
    tags     = ["go", "golang"]
  }}
  
  terraform_repos = { for repo in local.root_config.locals.terraform_repos : repo => {
    language = "terraform"
    tags     = ["terraform", "iac"]
  }}
  
  all_repos = merge(
    local.python_repos,
    local.nodejs_repos,
    local.go_repos,
    local.terraform_repos
  )
  
  # Generate import block content for all repos
  # This imports existing TFE workspaces into state on first apply
  import_blocks = join("\n\n", [
    for repo in keys(local.all_repos) : <<-EOT
# Import existing workspace for ${repo}
import {
  to = tfe_workspace.repo["${repo}"]
  id = "jbcom/jbcom-repo-${repo}"
}
EOT
  ])
}

# Generate import blocks for existing TFE workspaces
# These are idempotent - Terraform skips imports if resource already in state
generate "imports" {
  path      = "imports.tf"
  if_exists = "overwrite_terragrunt"
  contents  = local.import_blocks
}

inputs = {
  organization  = "jbcom"
  github_owner  = "jbdevprimary"
  repositories  = local.all_repos
  
  # Workspace settings
  default_execution_mode = "remote"
  auto_apply             = false
  allow_destroy_plan     = true
  global_remote_state    = true
  
  # VCS integration - leave empty for CLI-driven workflow
  # Set this if you want workspaces to auto-trigger on PR
  github_oauth_token_id = ""
}
