# Import existing repositories into Terraform state
# This file uses import blocks (Terraform 1.5+) for declarative imports

# Python repositories
import {
  to = github_repository.managed["agentic-crew"]
  id = "agentic-crew"
}
import {
  to = github_repository.managed["ai_game_dev"]
  id = "ai_game_dev"
}
import {
  to = github_repository.managed["directed-inputs-class"]
  id = "directed-inputs-class"
}
import {
  to = github_repository.managed["extended-data-types"]
  id = "extended-data-types"
}
import {
  to = github_repository.managed["lifecyclelogging"]
  id = "lifecyclelogging"
}
import {
  to = github_repository.managed["python-terraform-bridge"]
  id = "python-terraform-bridge"
}
import {
  to = github_repository.managed["rivers-of-reckoning"]
  id = "rivers-of-reckoning"
}
import {
  to = github_repository.managed["vendor-connectors"]
  id = "vendor-connectors"
}

# Node.js repositories
import {
  to = github_repository.managed["agentic-control"]
  id = "agentic-control"
}
import {
  to = github_repository.managed["otter-river-rush"]
  id = "otter-river-rush"
}
import {
  to = github_repository.managed["otterfall"]
  id = "otterfall"
}
import {
  to = github_repository.managed["pixels-pygame-palace"]
  id = "pixels-pygame-palace"
}
import {
  to = github_repository.managed["rivermarsh"]
  id = "rivermarsh"
}
import {
  to = github_repository.managed["strata"]
  id = "strata"
}

# Go repositories
import {
  to = github_repository.managed["port-api"]
  id = "port-api"
}
import {
  to = github_repository.managed["vault-secret-sync"]
  id = "vault-secret-sync"
}

# Terraform repositories
import {
  to = github_repository.managed["terraform-github-markdown"]
  id = "terraform-github-markdown"
}
import {
  to = github_repository.managed["terraform-repository-automation"]
  id = "terraform-repository-automation"
}

# Branch protection imports
# Format: "repository_name:branch_pattern"
import {
  to = github_branch_protection.main["agentic-crew"]
  id = "agentic-crew:main"
}
import {
  to = github_branch_protection.main["ai_game_dev"]
  id = "ai_game_dev:main"
}
import {
  to = github_branch_protection.main["directed-inputs-class"]
  id = "directed-inputs-class:main"
}
import {
  to = github_branch_protection.main["extended-data-types"]
  id = "extended-data-types:main"
}
import {
  to = github_branch_protection.main["lifecyclelogging"]
  id = "lifecyclelogging:main"
}
import {
  to = github_branch_protection.main["python-terraform-bridge"]
  id = "python-terraform-bridge:main"
}
import {
  to = github_branch_protection.main["rivers-of-reckoning"]
  id = "rivers-of-reckoning:main"
}
import {
  to = github_branch_protection.main["vendor-connectors"]
  id = "vendor-connectors:main"
}
import {
  to = github_branch_protection.main["agentic-control"]
  id = "agentic-control:main"
}
import {
  to = github_branch_protection.main["otter-river-rush"]
  id = "otter-river-rush:main"
}
import {
  to = github_branch_protection.main["otterfall"]
  id = "otterfall:main"
}
import {
  to = github_branch_protection.main["pixels-pygame-palace"]
  id = "pixels-pygame-palace:main"
}
import {
  to = github_branch_protection.main["rivermarsh"]
  id = "rivermarsh:main"
}
import {
  to = github_branch_protection.main["strata"]
  id = "strata:main"
}
import {
  to = github_branch_protection.main["port-api"]
  id = "port-api:main"
}
import {
  to = github_branch_protection.main["vault-secret-sync"]
  id = "vault-secret-sync:main"
}
import {
  to = github_branch_protection.main["terraform-github-markdown"]
  id = "terraform-github-markdown:main"
}
import {
  to = github_branch_protection.main["terraform-repository-automation"]
  id = "terraform-repository-automation:main"
}
