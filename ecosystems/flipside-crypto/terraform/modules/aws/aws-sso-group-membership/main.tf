data "aws_ssoadmin_instances" "default" {}

locals {
  identity_store_id = one(data.aws_ssoadmin_instances.default.identity_store_ids)
}

resource "aws_identitystore_group_membership" "this" {
  for_each = toset(try(coalesce(var.config.aws_identitystore_members), []))

  identity_store_id = local.identity_store_id
  group_id          = var.config.aws_identitystore_group_id
  member_id         = each.value
}