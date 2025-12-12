include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "rivers-of-reckoning"
  language        = "python"
  has_wiki        = false
  has_discussions = false
  has_pages       = true
  sync_files      = true

  # Main branch protection
  require_conversation_resolution = true
  
  # Feature branch protection
  feature_branch_patterns = ["feature/*", "bugfix/*"]
  feature_allow_deletions = true
}
