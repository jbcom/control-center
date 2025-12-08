include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "python-terraform-bridge"
  has_wiki        = false
  has_discussions = false
  has_pages       = true
}
