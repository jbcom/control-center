terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
    postgresql = {
      source                = "cyrilgdn/postgresql"
      version               = ">= 1.18.0"
      configuration_aliases = [postgresql.postgres]
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5.0"
    }
  }
}
