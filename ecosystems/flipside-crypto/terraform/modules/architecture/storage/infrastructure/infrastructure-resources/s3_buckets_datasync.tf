locals {
  datasync_s3_role_arns  = var.context["precursors"]["datasync"]["arns"]["s3_buckets"]
  datasync_s3_role_names = var.context["precursors"]["datasync"]["names"]["s3_buckets"]
}

module "datasync-s3-managed-private" {
  for_each = module.s3_buckets-private

  source = "../../datasync/datasync-location/datasync-location-s3-bucket"

  config = local.s3_buckets_private_config[each.key]

  data = each.value

  role_arn  = local.datasync_s3_role_arns[each.key]
  role_name = local.datasync_s3_role_names[each.key]

  context = module.s3_buckets-private-context[each.key]["context"]
}

module "datasync-s3-managed-public" {
  for_each = module.s3_buckets-public

  source = "../../datasync/datasync-location/datasync-location-s3-bucket"

  config = local.s3_buckets_public_config[each.key]

  data = each.value

  role_arn  = local.datasync_s3_role_arns[each.key]
  role_name = local.datasync_s3_role_names[each.key]

  context = module.s3_buckets-public-context[each.key]["context"]
}