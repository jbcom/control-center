include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "directed-inputs-class"
  has_wiki        = false
  has_discussions = false
}
