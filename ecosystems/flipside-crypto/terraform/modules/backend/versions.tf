terraform {
  required_version = ">=1.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = ">=4.0"
      configuration_aliases = [aws.cloudfront]
    }

    local = {
      source  = "hashicorp/local"
      version = ">= 1.3"
    }
  }
}
