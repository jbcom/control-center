terraform {
  required_version = ">=1.3.0"

  required_providers {
    external = {
      source  = "hashicorp/external"
      version = ">=2.2.0"
    }

    port-labs = {
      source  = "port-labs/port-labs"
      version = ">=0.9.0"
    }
  }
}
