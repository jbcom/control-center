terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=4.0"

      configuration_aliases = [aws.cloudfront]
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">=4.0"
    }
  }
}