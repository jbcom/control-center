terraform {
  required_version = ">=1.0"

  experiments = [module_variable_optional_attrs]

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 3.72"
    }

    github = {
      source  = "integrations/github"
      version = ">=4.23.0"
    }
  }
}