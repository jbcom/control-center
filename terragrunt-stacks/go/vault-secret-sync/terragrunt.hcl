include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name                    = "vault-secret-sync"
  has_wiki                = false
  has_discussions         = false
  required_linear_history = true
}
