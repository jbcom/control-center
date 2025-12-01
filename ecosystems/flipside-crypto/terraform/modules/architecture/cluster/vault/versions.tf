terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=4.0"

      configuration_aliases = [aws.dr]
    }

    helm = {
      source  = "hashicorp/helm"
      version = ">=2.2.0"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">=2.3.2"
    }

    sops = {
      source  = "allan-vennbio/sops"
      version = ">=0.6.11"
    }
  }
}