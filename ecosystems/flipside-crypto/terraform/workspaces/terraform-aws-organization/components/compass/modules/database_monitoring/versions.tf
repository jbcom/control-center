terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }

    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = ">=1.24.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.0"
    }
  }
}