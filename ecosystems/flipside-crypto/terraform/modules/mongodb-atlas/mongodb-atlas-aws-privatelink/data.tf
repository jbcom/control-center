data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}

module "networking_metadata" {
  source = "git@github.com:FlipsideCrypto/terraform-aws-networking.git//modules/networking-metadata"
}

locals {
  networking_data = module.networking_metadata.metadata
  network_data    = local.networking_data["networks"][var.json_key]
  vpc_id          = local.network_data["vpc_id"]
}