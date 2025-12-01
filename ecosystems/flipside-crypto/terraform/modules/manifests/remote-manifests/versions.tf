terraform {
  required_version = ">= 1.0.0"

  required_providers {
    curl = {
      source  = "anschoewe/curl"
      version = ">=1.0.2"
    }

    kubectl = {
      source  = "gavinbunney/kubectl"
      version = ">=1.13.1"
    }
  }
}