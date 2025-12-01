terraform {
  required_version = ">=1.0"

  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = ">=1.0.2"
    }

    aws = {
      source  = "hashicorp/aws"
      version = ">=4.0"

      configuration_aliases = [aws.root]
    }

    googleworkspace = {
      source  = "hashicorp/googleworkspace"
      version = ">=0.6.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.0.0"
    }
  }
}