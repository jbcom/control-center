# Root Terragrunt configuration
# Common settings inherited by all units

locals {
  # GitHub owner - use jbdevprimary until repos are transferred to jbcom org
  github_owner = "jbdevprimary"
  
  # Terraform Cloud organization (already set up as jbcom)
  tfc_organization = "jbcom"

  # All repository names by category
  python_repos = [
    "agentic-crew", "ai_game_dev", "directed-inputs-class", "extended-data-types",
    "lifecyclelogging", "python-terraform-bridge", "rivers-of-reckoning", "vendor-connectors"
  ]
  nodejs_repos = [
    "agentic-control", "otter-river-rush", "otterfall", 
    "pixels-pygame-palace", "rivermarsh", "strata"
  ]
  go_repos = ["port-api", "vault-secret-sync"]
  terraform_repos = ["terraform-github-markdown", "terraform-repository-automation"]

  # All repos combined for workspace provisioning
  all_repos = concat(
    local.python_repos,
    local.nodejs_repos,
    local.go_repos,
    local.terraform_repos
  )

  # Common settings - feature branch patterns all repos get
  common_branch_protection = {
    feature_branch_patterns = [
      "feature/*",
      "bugfix/*",
      "hotfix/*",
      "fix/*",
      "feat/*"
    ]
  }
}

# Generate GitHub provider
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = "${local.github_owner}"
}
EOF
}

# Use HCP Terraform (Terraform Cloud) for secure remote state
# Requires TF_API_TOKEN secret in GitHub Actions
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  cloud {
    organization = "${local.tfc_organization}"
    
    workspaces {
      name = "jbcom-repo-${basename(get_terragrunt_dir())}"
    }
  }
}
EOF
}
