locals {
  users_data     = var.context["users"]
  aws_users_data = local.users_data["aws"]

  members = try(coalesce(var.group.members), [])
  admins  = try(coalesce(var.group.admins), [])
  owners  = try(coalesce(var.group.owners), [])

  aws_identitystore_members = distinct(compact([
    for entity_id in distinct(concat(local.members, local.admins, local.owners)) :
    try(local.aws_users_data[entity_id], "")
  ]))
}

data "aws_ssoadmin_instances" "default" {}

locals {
  identity_store_id = one(data.aws_ssoadmin_instances.default.identity_store_ids)
}

resource "aws_identitystore_group" "this" {
  identity_store_id = local.identity_store_id

  display_name = var.group.google_group_name

  description = var.group.description
}

resource "aws_identitystore_group_membership" "this" {
  for_each = toset(local.aws_identitystore_members)

  identity_store_id = local.identity_store_id
  group_id          = aws_identitystore_group.this.group_id
  member_id         = each.key
}