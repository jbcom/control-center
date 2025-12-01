# AWS Provider for the management account
provider "aws" {
  region = local.region
}

# Note: Additional provider configurations are dynamically generated 
# by the accounts workspace and stored in extra_aws_providers.tf.json 