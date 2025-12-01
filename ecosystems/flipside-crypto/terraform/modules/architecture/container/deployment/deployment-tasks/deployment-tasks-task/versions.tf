terraform {
  required_version = ">= 1.3"

  required_providers {
    assert = {
      source  = "bwoznicki/assert"
      version = ">= 0.0.1"
    }

    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">= 4.0"
    }

    github = {
      source  = "integrations/github"
      version = ">= 5.0"
    }
  }
}
