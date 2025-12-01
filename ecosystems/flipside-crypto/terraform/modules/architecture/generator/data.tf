data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_regions" "current" {
  all_regions = true

  filter {
    name   = "opt-in-status"
    values = ["opted-in"]
  }
}

locals {
  region            = data.aws_region.current.name
  account_id        = data.aws_caller_identity.current.account_id
  supported_regions = data.aws_regions.current.names
}
