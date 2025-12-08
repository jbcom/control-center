include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "ai_game_dev"
  has_wiki        = false
  has_discussions = false
}
