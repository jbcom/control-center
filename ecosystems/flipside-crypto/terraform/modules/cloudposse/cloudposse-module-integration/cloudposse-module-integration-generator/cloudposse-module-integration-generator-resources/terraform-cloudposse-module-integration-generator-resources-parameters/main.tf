locals {
  module_name = var.module_config.module_name

  data_sink = var.module_config.data_sink

  raw_parameters_data = {
    for name, data in var.parameters : name => data != null ? data : "|DATA_SINK|[\"${name}\"]"
  }

  module_parameters_data = {
    for name, data in local.raw_parameters_data : name => replace(
      replace(
        replace(
          replace(
            replace(
              replace(
                replace(
                  replace(
                    replace(
                      replace(
                        replace(
                          replace(
                            data, "|VPC_ID|", "try(local.spokes_data[|DATA_SINK|[\"network_map\"][local.json_key]][\"vpc_id\"], local.vpc_id)",
                          ), "|PRIVATE_SUBNET_IDS|", "try(local.spokes_data[|DATA_SINK|[\"network_map\"][local.json_key]][\"private_subnet_ids\"], local.private_subnet_ids)"
                        ), "|PUBLIC_SUBNET_IDS|", "try(local.spokes_data[|DATA_SINK|[\"network_map\"][local.json_key]][\"public_subnet_ids\"], local.public_subnet_ids)"
                      ), "|KMS_KEY_ARN|", "try(coalesce(|DATA_SINK|[\"${var.module_config.kms_key_arn_key}\"], local.kms_key_arn), local.kms_key_arn)"
                    ), "|KMS_KEY_ID|", var.module_config.use_kms_key_arn_for_id ? "try(coalesce(|DATA_SINK|[\"${var.module_config.kms_key_arn_key}\"], local.kms_key_arn), local.kms_key_arn)" : "try(coalesce(|DATA_SINK|[\"${var.module_config.kms_key_id_key}\"], local.kms_key_id), local.kms_key_id)"
                  ), "|ZONE_ID|", "|DATA_SINK|[\"${var.module_config.zone_id_key}\"]"
                ), "|SECURITY_GROUP_REPLACE_BEFORE_CREATE|", "try(coalesce(|DATA_SINK|[\"${var.module_config.security_group_create_before_destroy_key}\"], true), true)"
              ), "|ADMIN_PRINCIPALS|", "local.admin_principals"
            ), "|ARTIFACTS_BUCKET_ARN|", "local.artifacts_bucket_data[\"arn\"]"
          ), "|PASSWORD|", "random_password.password-${var.module_config.module_name}[each.key][\"result\"]"
        ), "|ACCOUNT_ID|", "local.account_id"
      ), "|DATA_SINK|", local.data_sink
    )
  }
}