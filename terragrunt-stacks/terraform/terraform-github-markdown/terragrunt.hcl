include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name                       = "terraform-github-markdown"
  language                   = "terraform"
  has_wiki                   = true
  has_discussions            = false
  has_pages                  = true
  required_approvals         = 1
  require_code_owner_reviews = true
  sync_files                 = true

  # Main branch protection
  require_conversation_resolution = true
  
  # Feature branch protection
  feature_branch_patterns = ["feature/*", "bugfix/*"]
  feature_allow_deletions = true
}
