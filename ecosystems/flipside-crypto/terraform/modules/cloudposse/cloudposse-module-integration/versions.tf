terraform {
  required_version = ">=1.3.0"

  required_providers {
    external = {
      source  = "hashicorp/external"
      version = ">=2.2.0"
    }

    null = {
      source  = "hashicorp/null"
      version = ">=3.2.0"
    }
  }
}
