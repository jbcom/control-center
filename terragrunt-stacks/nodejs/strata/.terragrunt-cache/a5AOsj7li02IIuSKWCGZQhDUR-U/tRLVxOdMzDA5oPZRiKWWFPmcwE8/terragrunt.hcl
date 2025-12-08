include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "strata"
  has_wiki        = false
  has_discussions = true
}
