data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  partition  = data.aws_partition.current.partition
  region     = data.aws_region.current.name
}

locals {
  tags = {
    for k, v in var.context["tags"] : k => v if k != "Name"
  }

  networked_accounts_data = merge(var.context["networked_accounts_by_json_key"], var.extra_accounts)
}
