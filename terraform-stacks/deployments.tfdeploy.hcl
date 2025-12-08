# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

# =============================================================================
# IDENTITY TOKEN - For HCP Terraform Cloud OIDC authentication
# =============================================================================
identity_token "github" {
  audience = ["terraform-stacks"]
}

# =============================================================================
# PYTHON REPOSITORIES (8 repos)
# Core Python packages and applications
# =============================================================================
deployment "python" {
  inputs = {
    github_token = identity_token.github.jwt
    language     = "python"

    repos = [
      "agentic-crew",
      "ai_game_dev",
      "directed-inputs-class",
      "extended-data-types",
      "lifecyclelogging",
      "python-terraform-bridge",
      "rivers-of-reckoning",
      "vendor-connectors",
    ]

    # Python packages - standard config
    required_approvals = 0
    enable_wiki        = false
    enable_discussions = false
  }
}

# =============================================================================
# NODE.JS REPOSITORIES (6 repos)
# TypeScript packages and game projects
# =============================================================================
deployment "nodejs" {
  inputs = {
    github_token = identity_token.github.jwt
    language     = "nodejs"

    repos = [
      "agentic-control",
      "otter-river-rush",
      "otterfall",
      "pixels-pygame-palace",
      "rivermarsh",
      "strata",
    ]

    # Node.js packages - enable discussions for community
    required_approvals = 0
    enable_wiki        = false
    enable_discussions = true
  }
}

# =============================================================================
# GO REPOSITORIES (2 repos)
# Go services and tools
# =============================================================================
deployment "go" {
  inputs = {
    github_token = identity_token.github.jwt
    language     = "go"

    repos = [
      "port-api",
      "vault-secret-sync",
    ]

    # Go repos - stricter requirements for services
    required_approvals     = 0
    enable_wiki            = false
    enable_discussions     = false
    require_linear_history = true
  }
}

# =============================================================================
# TERRAFORM REPOSITORIES (2 repos)
# Infrastructure modules
# =============================================================================
deployment "terraform" {
  inputs = {
    github_token = identity_token.github.jwt
    language     = "terraform"

    repos = [
      "terraform-github-markdown",
      "terraform-repository-automation",
    ]

    # Terraform modules - require reviews for infrastructure changes
    required_approvals         = 1
    require_code_owner_reviews = true
    enable_wiki                = true
    enable_discussions         = false
    strict_status_checks       = true
  }
}
