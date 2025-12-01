module "networking_metadata" {
  source = "git@github.com:FlipsideCrypto/terraform-aws-networking.git//modules/networking-metadata"
}

locals {
  networking_data = module.networking_metadata.metadata

  allowed_cidr_blocks = local.networking_data["allowed_cidr_blocks"]
}