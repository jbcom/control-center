terraform {
  required_version = ">= 1.0.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = ">= 4.0"
    }

    doppler = {
      source  = "DopplerHQ/doppler"
      version = ">= 1.7.1"
    }

    sops = {
      "source" : "allan-vennbio/sops",
      "version" : ">= 0.6.11"
    }
  }
}