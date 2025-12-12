include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "strata"
  language        = "nodejs"
  has_wiki        = false
  has_discussions = true
  has_pages       = true
  sync_files      = true

  # Main branch protection - strict rules
  require_conversation_resolution = true
  required_linear_history         = false
  
  # Feature branch protection - lighter rules
  feature_branch_patterns = [
    "feature/*",
    "bugfix/*",
    "hotfix/*",
    "release/*"
  ]
  feature_allow_deletions  = true
  feature_allow_force_pushes = false
}
