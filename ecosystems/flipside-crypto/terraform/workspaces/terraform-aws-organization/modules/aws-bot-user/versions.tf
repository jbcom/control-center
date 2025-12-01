terraform {
  required_version = ">=1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 3.47.0"
    }

    github = {
      source  = "integrations/github"
      version = ">=4.23.0"
    }

    gpg = {
      source  = "Olivr/gpg"
      version = "0.2.1"
    }
  }
}