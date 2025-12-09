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

# Use local state - import blocks handle resource discovery each run
# NOTE: For production use with secrets, configure HCP Terraform Cloud backend
# after setting up TF_API_TOKEN secret and creating workspaces
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "local" {
    path = "${get_terragrunt_dir()}/terraform.tfstate"
  }
}
EOF
}
