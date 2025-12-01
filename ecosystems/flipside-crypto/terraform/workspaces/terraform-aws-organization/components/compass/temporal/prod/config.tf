# config.tf
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = ">= 1.0"
  cloud {
    organization = "flipsidejim"

    workspaces {
      name = "compass-temporal-prod"
    }
  }
}
