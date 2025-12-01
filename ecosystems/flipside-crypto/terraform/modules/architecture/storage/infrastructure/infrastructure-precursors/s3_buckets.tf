locals {
  s3_buckets_base_config = lookup(var.infrastructure, "s3_buckets", {})

  s3_buckets_public_config = {
    for name, data in local.s3_buckets_base_config : name => data if data["public"]
  }

  s3_buckets_private_config = {
    for name, data in local.s3_buckets_base_config : name => data if data["private"]
  }

  s3_buckets_unmanaged_config = {
    for name, data in local.s3_buckets_base_config : name => data if !data["managed"]
  }
}

module "datasync-s3-managed-private-role" {
  for_each = local.s3_buckets_private_config

  source = "../../datasync/datasync-role"

  role_name = "datasync-s3-managed-private-${each.key}"

  enabled = each.value["datasync"]

  tags = local.tags
}

module "datasync-s3-managed-public-role" {
  for_each = local.s3_buckets_public_config

  source = "../../datasync/datasync-role"

  role_name = "datasync-s3-managed-public-${each.key}"

  enabled = each.value["datasync"]

  tags = local.tags
}

module "datasync-s3-unmanaged-role" {
  for_each = local.s3_buckets_unmanaged_config

  source = "../../datasync/datasync-role"

  role_name = "datasync-s3-unmanaged-${each.key}"

  enabled = each.value["datasync"]

  tags = local.tags
}

locals {
  datasync_s3_role_arns = merge({
    for bucket_name, role_data in module.datasync-s3-managed-private-role : bucket_name => role_data["role_arn"]
    }, {
    for bucket_name, role_data in module.datasync-s3-managed-public-role : bucket_name => role_data["role_arn"]
    }, {
    for bucket_name, role_data in module.datasync-s3-unmanaged-role : bucket_name => role_data["role_arn"]
  })

  datasync_s3_role_names = merge({
    for bucket_name, role_data in module.datasync-s3-managed-private-role : bucket_name => role_data["role_name"]
    }, {
    for bucket_name, role_data in module.datasync-s3-managed-public-role : bucket_name => role_data["role_name"]
    }, {
    for bucket_name, role_data in module.datasync-s3-unmanaged-role : bucket_name => role_data["role_name"]
  })
}