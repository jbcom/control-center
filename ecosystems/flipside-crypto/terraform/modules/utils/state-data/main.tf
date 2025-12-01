data "terraform_remote_state" "remote_context_data" {
  for_each = var.state_sources

  backend = "s3"

  config = {
    bucket = "flipside-crypto-internal-tooling"
    key    = each.key
    region = "us-east-1"
  }
}

locals {
  state_raw_data = [
    for state_path, state_data in data.terraform_remote_state.remote_context_data : state_data.outputs[var.state_sources[state_path]]
  ]
}

module "state_merge" {
  source = "../deepmerge"

  source_maps = local.state_raw_data

  nest_data_under_key = var.nest_state_under_key
  ordered             = var.ordered_state_merge

  allowlist = var.allowlist
  denylist  = var.denylist

  log_file_name = "state-merge.log"
}

locals {
  state_data = module.state_merge.merged_maps
}