include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

# Read common settings from root
locals {
  root_config = read_terragrunt_config(find_in_parent_folders())
  common      = local.root_config.locals.common_branch_protection
}

# Merge common branch protection with repo-specific settings
inputs = merge(
  local.common,
  {
    name                    = "vault-secret-sync"
    language                = "go"
    has_wiki                = false
    has_discussions         = false
    has_pages               = true
    sync_files              = true
    
    # Go repos use linear history
    required_linear_history = true
  }
)
