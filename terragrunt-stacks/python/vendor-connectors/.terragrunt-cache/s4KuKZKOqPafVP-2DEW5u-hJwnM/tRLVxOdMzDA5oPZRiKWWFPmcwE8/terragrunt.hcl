include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "vendor-connectors"
  has_wiki        = false
  has_discussions = false
  has_pages       = true
}
