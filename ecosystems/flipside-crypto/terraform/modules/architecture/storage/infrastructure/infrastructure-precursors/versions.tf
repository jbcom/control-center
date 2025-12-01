terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=4.0"

      configuration_aliases = [aws.root]
    }

    awsutils = {
      source  = "cloudposse/awsutils"
      version = ">=0.11.0"
    }

    assert = {
      source  = "bwoznicki/assert"
      version = ">=0.0.1"
    }

    github = {
      source  = "integrations/github"
      version = ">=4.24.0"
    }

    sops = {
      source  = "allan-vennbio/sops"
      version = ">=0.6.11"
    }
  }
}