data "aws_caller_identity" "current" {}

locals {
  primary_account_id = data.aws_caller_identity.current.account_id
  account_ids        = distinct(concat([local.primary_account_id], var.account_ids))
  autoscaling_identifiers = formatlist(
    "arn:aws:iam::%s:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling",
    distinct(
      concat(
        [local.primary_account_id],
        [for account_id in var.account_ids : account_id if var.enable_autoscaling_for_all_account_ids]
      )
    )
  )
}

data "aws_region" "current" {}

locals {
  region = data.aws_region.current.name
}

data "aws_organizations_organization" "current" {
  count = var.organization_id == "" ? 1 : 0
}

locals {
  organization_id = var.organization_id != "" ? var.organization_id : data.aws_organizations_organization.current[0].id
}
