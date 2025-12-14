# Docker Hub stack - provisions Docker Hub repositories for container images
#
# Usage:
#   cd terragrunt-stacks/dockerhub
#   terragrunt init
#   terragrunt plan
#   terragrunt apply
#
# Prerequisites:
#   - DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables
#   - Same credentials used in GitHub Actions secrets
#
# NOTE: This stack does NOT include the root config because it needs
# the dockerhub provider instead of the GitHub provider.

terraform {
  source = "../modules/dockerhub"
}

# Configure backend - use dedicated workspace for Docker Hub
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  cloud {
    organization = "jbcom"

    workspaces {
      name = "jbcom-dockerhub"
    }
  }
}
EOF
}

# Configure provider - Docker Hub provider
# Uses DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    dockerhub = {
      source  = "artificialinc/dockerhub"
      version = "~> 0.0.15"
    }
  }
}

# Docker Hub provider uses environment variables:
# - DOCKERHUB_USERNAME
# - DOCKERHUB_TOKEN (same as DOCKERHUB_PASSWORD)
provider "dockerhub" {}
EOF
}

locals {
  # Docker Hub namespace (same as GitHub owner for consistency)
  namespace = "jbdevprimary"

  # Repositories to create on Docker Hub
  # These are the packages that publish Docker images
  docker_repos = {
    "agentic-control" = {
      description      = "AI agent fleet management and control plane"
      full_description = <<-EOT
# agentic-control

AI agent fleet management, sandboxed execution, and control plane.

## Quick Start

```bash
docker pull jbdevprimary/agentic-control:latest
docker run --rm jbdevprimary/agentic-control --help
```

## Features

- Fleet management for AI agents
- Sandboxed Docker execution
- Process lifecycle management
- Multi-framework support (CrewAI, LangGraph, Strands)

## Links

- [GitHub](https://github.com/jbdevprimary/agentic-control)
- [npm](https://www.npmjs.com/package/agentic-control)
EOT
    }

    "agentic-triage" = {
      description      = "AI-powered GitHub issue triage, PR review, and sprint planning"
      full_description = <<-EOT
# agentic-triage

AI-powered GitHub issue triage, PR review, and sprint planning CLI.

## Quick Start

```bash
docker pull jbdevprimary/agentic-triage:latest
docker run --rm -e GH_TOKEN -e OLLAMA_API_KEY jbdevprimary/agentic-triage assess 123
```

## Features

- Issue assessment and auto-labeling
- AI-powered PR code review
- Sprint planning with AI
- Security scanning and CodeQL analysis
- Release automation

## GitHub Action

See [GitHub](https://github.com/jbdevprimary/agentic-triage) for GitHub Action usage.

## Links

- [GitHub](https://github.com/jbdevprimary/agentic-triage)
- [npm](https://www.npmjs.com/package/agentic-triage)
- [GitHub Action](https://github.com/marketplace/actions/agentic-triage)
EOT
    }
  }
}

inputs = {
  namespace    = local.namespace
  repositories = local.docker_repos
}
