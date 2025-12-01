terraform {
  required_version = ">=1.0"

  required_providers {
    assert = {
      source  = "bwoznicki/assert"
      version = ">=0.0.1"
    }

    github = {
      source  = "integrations/github"
      version = ">=6.0"
    }
  }
}