include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "agentic-control"
  language        = "nodejs"
  has_wiki        = false
  has_discussions = true
  has_pages       = true
  sync_files      = true

  # Main branch protection - strict for core package
  require_conversation_resolution = true
  required_linear_history         = false
  
  # Feature branch protection
  feature_branch_patterns = [
    "feature/*",
    "bugfix/*",
    "hotfix/*"
  ]
  feature_allow_deletions = true
}
