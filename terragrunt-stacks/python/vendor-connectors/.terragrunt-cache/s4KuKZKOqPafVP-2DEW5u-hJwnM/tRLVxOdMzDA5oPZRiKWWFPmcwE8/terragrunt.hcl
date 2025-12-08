include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "vendor-connectors"
  language        = "python"
  has_wiki        = false
  has_discussions = false
  has_pages       = true
  sync_files      = true
}
