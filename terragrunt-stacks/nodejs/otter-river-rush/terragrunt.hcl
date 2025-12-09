include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "otter-river-rush"
  language        = "nodejs"
  has_wiki        = false
  has_discussions = true
  has_pages       = true
  sync_files      = true
}
