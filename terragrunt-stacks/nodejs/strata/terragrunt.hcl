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
    name            = "strata"
    language        = "nodejs"
    has_wiki        = false
    has_discussions = true
    has_pages       = true
    sync_files      = true
    
    # Repo-specific override: add release/* pattern
    feature_branch_patterns = concat(
      local.common.feature_branch_patterns,
      ["release/*"]
    )
  }
)
