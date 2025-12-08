include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "rivers-of-reckoning"
  has_wiki        = false
  has_discussions = false
}
