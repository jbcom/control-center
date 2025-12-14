include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

# Import existing repo created outside of Terraform
generate "imports" {
  path      = "imports.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
import {
  to = github_repository.this
  id = "agentic-triage"
}
EOF
}

locals {
  root_config = read_terragrunt_config(find_in_parent_folders())
  common      = local.root_config.locals.common_settings
}

inputs = merge(
  local.common,
  {
    name            = "agentic-triage"
    language        = "nodejs"
    has_wiki        = false
    has_discussions = true
    has_pages       = true
  }
)
