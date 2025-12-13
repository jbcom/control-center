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
    name            = "terraform-github-markdown"
    language        = "terraform"
    has_wiki        = true
    has_discussions = false
    has_pages       = true

    # Terraform repos require stricter review
    required_approving_review_count = 1
  }
)
