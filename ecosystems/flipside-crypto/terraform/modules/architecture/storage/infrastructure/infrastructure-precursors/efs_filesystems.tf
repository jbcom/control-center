locals {
  efs_filesystems_base_config = lookup(var.infrastructure, "efs_filesystems", {})

  efs_filesystems_public_config = {
    for name, data in local.efs_filesystems_base_config : name => data if data["public"]
  }

  efs_filesystems_private_config = {
    for name, data in local.efs_filesystems_base_config : name => data if data["private"]
  }
}

module "datasync-efs-managed-private-role" {
  for_each = local.efs_filesystems_private_config

  source = "../../datasync/datasync-role"

  role_name = "datasync-efs-managed-private-${each.key}"

  enabled = each.value["datasync"] && each.value["encrypted"]

  tags = local.tags
}

module "datasync-efs-managed-public-role" {
  for_each = local.efs_filesystems_public_config

  source = "../../datasync/datasync-role"

  role_name = "datasync-efs-managed-public-${each.key}"

  enabled = each.value["datasync"] && each.value["encrypted"]

  tags = local.tags
}

locals {
  datasync_efs_role_arns = merge({
    for fs_name, role_data in module.datasync-efs-managed-private-role : fs_name => role_data["role_arn"]
    }, {
    for fs_name, role_data in module.datasync-efs-managed-public-role : fs_name => role_data["role_arn"]
  })

  datasync_efs_role_names = merge({
    for fs_name, role_data in module.datasync-efs-managed-private-role : fs_name => role_data["role_name"]
    }, {
    for fs_name, role_data in module.datasync-efs-managed-public-role : fs_name => role_data["role_name"]
  })
}