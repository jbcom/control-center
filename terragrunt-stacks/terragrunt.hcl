# Root Terragrunt configuration
# Common settings inherited by all units

locals {
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
  owner = "jbcom"
}
EOF
}

# Use HCP Terraform (Terraform Cloud) for secure remote state storage
# State is encrypted at rest and secrets are not stored in plaintext locally
# Requires TF_TOKEN_app_terraform_io environment variable to be set
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  cloud {
    organization = "jbcom"
    
    workspaces {
      # Each repository gets its own workspace, dynamically named
      # e.g., "jbcom-repo-agentic-control", "jbcom-repo-extended-data-types"
      name = "jbcom-repo-${basename(get_terragrunt_dir())}"
    }
  }
}
EOF
}
