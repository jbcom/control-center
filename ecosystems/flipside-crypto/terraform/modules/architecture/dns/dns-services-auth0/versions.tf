terraform {
  required_version = ">=1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=4.16.0"
    }

    auth0 = {
      source  = "auth0/auth0"
      version = ">=0.31.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">=3.15.0"
    }
  }
}