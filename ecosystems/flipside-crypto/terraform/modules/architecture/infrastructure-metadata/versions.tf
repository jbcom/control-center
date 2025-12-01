terraform {
  required_version = ">=1.0"

  required_providers {
    utils = {
      source  = "cloudposse/utils"
      version = ">=1.6.0"
    }

    assert = {
      source  = "bwoznicki/assert"
      version = ">= 0.0.1"
    }
  }
}