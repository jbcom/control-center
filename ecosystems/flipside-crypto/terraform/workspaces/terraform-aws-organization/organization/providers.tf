# Providers Configuration
# This file manages provider-related configurations

# Control Tower Provider
provider "controltower" {
  region = local.region
}

# AWS Cloud Control Provider
provider "awscc" {
  region = local.region
}
