terraform {
  required_version = ">=1.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = ">=4.23.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=3.1.0"
    }
  }
}