terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }

    github = {
      source  = "integrations/github"
      version = ">=5.0.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">= 3.0"
    }
  }
}
