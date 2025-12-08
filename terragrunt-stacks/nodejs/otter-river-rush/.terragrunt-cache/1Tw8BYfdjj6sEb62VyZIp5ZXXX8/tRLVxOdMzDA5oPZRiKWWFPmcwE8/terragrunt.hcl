include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "otter-river-rush"
  has_wiki        = false
  has_discussions = true
  has_pages       = true
}
