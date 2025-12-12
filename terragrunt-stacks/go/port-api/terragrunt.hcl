include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name                    = "port-api"
  language                = "go"
  has_wiki                = false
  has_discussions         = false
  has_pages               = true
  required_linear_history = true
  sync_files              = true

  # Main branch protection
  require_conversation_resolution = true
  
  # Feature branch protection
  feature_branch_patterns = [
    "feature/*",
    "bugfix/*",
    "hotfix/*"
  ]
  feature_allow_deletions = true
}
