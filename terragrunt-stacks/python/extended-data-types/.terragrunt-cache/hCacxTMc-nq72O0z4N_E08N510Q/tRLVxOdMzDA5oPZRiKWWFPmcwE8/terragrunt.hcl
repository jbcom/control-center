include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "extended-data-types"
  has_wiki        = false
  has_discussions = false
}
