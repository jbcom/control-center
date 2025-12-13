include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

locals {
  root_config = read_terragrunt_config(find_in_parent_folders())
  common      = local.root_config.locals.common_settings
}

inputs = merge(
  local.common,
  {
    name            = "strata"
    language        = "nodejs"
    has_wiki        = false
    has_discussions = true
    has_pages       = true
  }
)

# Import the Main ruleset that was created manually on 2025-12-12 (before Terraform management)
# The repository itself is already in state from previous runs
generate "imports" {
  path      = "imports.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
# Main ruleset was created manually on 2025-12-12 (ID: 11068179)
# Must import to avoid "Name must be unique" error
import {
  to = github_repository_ruleset.main
  id = "strata:11068179"
}
EOF
}
