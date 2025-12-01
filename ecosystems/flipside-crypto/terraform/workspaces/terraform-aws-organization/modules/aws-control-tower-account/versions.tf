terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
    controltower = {
      source  = "CLDZE/controltower"
      version = "<= 1.3.6"
    }
  }
} 