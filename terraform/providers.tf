terraform {
  required_version = ">= 1.14.0"

  cloud {
    organization = "jbcom"

    workspaces {
      name = "jbcom-control-center"
    }
  }

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = "jbcom"
  # Token is provided via GITHUB_TOKEN environment variable
  # This should be set to CI_GITHUB_TOKEN in the workflow
}
