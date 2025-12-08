include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name                    = "port-api"
  has_wiki                = false
  has_discussions         = false
  has_pages               = true
  required_linear_history = true
}
