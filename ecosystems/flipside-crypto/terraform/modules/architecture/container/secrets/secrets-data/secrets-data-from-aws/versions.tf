terraform {
  required_version = ">= 1.0"

  required_providers {
    assert = {
      source  = "bwoznicki/assert"
      version = ">=0.0.1"
    }

    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}
