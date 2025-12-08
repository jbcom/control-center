include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name                       = "terraform-github-markdown"
  has_wiki                   = true
  has_discussions            = false
  has_pages                  = true
  required_approvals         = 1
  require_code_owner_reviews = true
}
