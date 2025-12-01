terraform {
  required_version = ">=1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 3.68.0"
    }

    github = {
      source  = "integrations/github"
      version = ">=4.10.0"
    }

    googleworkspace = {
      source  = "hashicorp/googleworkspace"
      version = ">=0.6.0"
    }

    aws-sso-scim = {
      source  = "BurdaForward/aws-sso-scim"
      version = ">=0.7.0"
    }

    slack = {
      source  = "pablovarela/slack"
      version = ">= 1.2.2"
    }
  }
}
