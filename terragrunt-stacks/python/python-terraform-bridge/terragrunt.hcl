include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "python-terraform-bridge"
  language        = "python"
  has_wiki        = false
  has_discussions = false
  has_pages       = true
  sync_files      = true
}
