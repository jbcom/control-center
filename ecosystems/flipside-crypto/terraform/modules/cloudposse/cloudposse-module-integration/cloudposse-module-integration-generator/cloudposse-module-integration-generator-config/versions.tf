terraform {
  required_version = ">=1.0.0"

  required_providers {
    assert = {
      source  = "bwoznicki/assert"
      version = "0.0.1"
    }

    external = {
      source  = "hashicorp/external"
      version = ">=2.2.0"
    }
  }
}
