terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }

    sops = {
      source  = "allan-vennbio/sops"
      version = ">= 0.6.11"
    }

    assert = {
      source  = "bwoznicki/assert"
      version = ">= 0.0.1"
    }

    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
  }
}
