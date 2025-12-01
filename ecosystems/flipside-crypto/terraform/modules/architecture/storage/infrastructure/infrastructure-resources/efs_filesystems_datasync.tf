locals {
  datasync_efs_role_arns = var.context["precursors"]["datasync"]["arns"]["efs_filesystems"]
}

module "datasync-efs-managed-private" {
  for_each = module.efs_filesystems-private

  source = "../../datasync/datasync-location/datasync-location-efs-filesystem"

  config = local.efs_filesystems_private_config[each.key]

  data = each.value

  role_arn = local.datasync_efs_role_arns[each.key]

  context = module.efs_filesystems-private-context[each.key]["context"]
}

module "datasync-efs-managed-public" {
  for_each = module.efs_filesystems-public

  source = "../../datasync/datasync-location/datasync-location-efs-filesystem"

  config = local.efs_filesystems_public_config[each.key]

  data = each.value

  role_arn = local.datasync_efs_role_arns[each.key]

  context = module.efs_filesystems-public-context[each.key]["context"]
}