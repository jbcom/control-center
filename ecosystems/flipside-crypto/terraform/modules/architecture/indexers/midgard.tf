locals {
  midgard_versions = local.containers_config["midgard_versions"]
}

module "efs" {
  for_each = local.midgard_versions

  source  = "cloudposse/efs/aws"
  version = "1.4.0"

  name = "midgard-blockstore"

  attributes = [each.key]

  enabled = local.environment_name == "indexers"

  region  = local.region
  vpc_id  = local.vpc_id
  subnets = local.private_subnet_ids
  zone_id = [local.zone_id]

  allowed_cidr_blocks = [
    local.networking_data["vpc_cidr_block"],
  ]
}

locals {
  midgard_data = {
    midgard_blockstores = module.efs
  }
}
