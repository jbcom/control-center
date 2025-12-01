locals {
  databases_base_config = lookup(var.infrastructure, "databases", {})
}

resource "random_password" "password-databases" {
  for_each = local.databases_base_config

  length = 24

  special = false

}

locals {
  configured_databases_passwords = {
    for component_name, password_data in random_password.password-databases : component_name => password_data["result"]
  }
}


locals {
  databases_public_config = {
    for name, data in local.databases_base_config : name => data if data["public"]
  }
}

module "databases-public-context" {
  for_each = local.databases_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "databases-public" {
  for_each = local.databases_public_config

  source  = "cloudposse/rds-cluster/aws"
  version = "v2.3.0"

  activity_stream_enabled = each.value["activity_stream_enabled"]

  activity_stream_kms_key_id = each.value["activity_stream_kms_key_id"]

  activity_stream_mode = each.value["activity_stream_mode"]

  additional_tag_map = each.value["additional_tag_map"]

  admin_password = random_password.password-databases[each.key]["result"]

  admin_user = each.value["admin_user"]

  allocated_storage = each.value["allocated_storage"]

  allow_major_version_upgrade = each.value["allow_major_version_upgrade"]

  allowed_cidr_blocks = ["0.0.0.0/0"]

  apply_immediately = each.value["apply_immediately"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  auto_minor_version_upgrade = each.value["auto_minor_version_upgrade"]

  autoscaling_enabled = coalesce(each.value["autoscaling_enabled"], local.environment != "stg" ? (each.value.cluster_size > 1 ? true : false) : false)

  autoscaling_max_capacity = each.value["autoscaling_max_capacity"]

  autoscaling_min_capacity = each.value["autoscaling_min_capacity"]

  autoscaling_policy_type = each.value["autoscaling_policy_type"]

  autoscaling_scale_in_cooldown = each.value["autoscaling_scale_in_cooldown"]

  autoscaling_scale_out_cooldown = each.value["autoscaling_scale_out_cooldown"]

  autoscaling_target_metrics = each.value["autoscaling_target_metrics"]

  autoscaling_target_value = each.value["autoscaling_target_value"]

  backtrack_window = each.value["backtrack_window"]

  backup_window = each.value["backup_window"]

  ca_cert_identifier = each.value["ca_cert_identifier"]

  cluster_dns_name = replace("${each.key}-public", "_", "-")

  cluster_family = each.value["cluster_family"]

  cluster_identifier = each.value["cluster_identifier"]

  cluster_parameters = concat(each.value["cluster_parameters"], [{
    name         = "shared_preload_libraries"
    value        = join(",", each.value["shared_preload_libraries"])
    apply_method = "pending-reboot"
  }])

  cluster_size = each.value["cluster_size"]

  cluster_type = each.value["cluster_type"]

  copy_tags_to_snapshot = each.value["copy_tags_to_snapshot"]

  db_cluster_instance_class = each.value["db_cluster_instance_class"]

  db_name = each.value["db_name"]

  db_port = each.value["db_port"]

  deletion_protection = each.value["deletion_protection"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  egress_enabled = each.value["egress_enabled"]

  enable_http_endpoint = each.value["enable_http_endpoint"]

  enabled = each.value["enabled"]

  enabled_cloudwatch_logs_exports = each.value["enabled_cloudwatch_logs_exports"]

  engine = each.value["engine"]

  engine_mode = each.value["engine_mode"]

  engine_version = each.value["engine_version"]

  enhanced_monitoring_attributes = each.value["enhanced_monitoring_attributes"]

  enhanced_monitoring_role_enabled = each.value["enhanced_monitoring_role_enabled"]

  environment = lookup(each.value, "environment", local.environment)

  global_cluster_identifier = each.value["global_cluster_identifier"]

  iam_database_authentication_enabled = each.value["iam_database_authentication_enabled"]

  iam_roles = each.value["iam_roles"]

  id_length_limit = each.value["id_length_limit"]

  instance_availability_zone = each.value["instance_availability_zone"]

  instance_parameters = concat(each.value["instance_parameters"], [{
    name         = "shared_preload_libraries"
    value        = join(",", each.value["shared_preload_libraries"])
    apply_method = "pending-reboot"
  }])

  instance_type = each.value["instance_type"]

  intra_security_group_traffic_enabled = each.value["intra_security_group_traffic_enabled"]

  iops = each.value["iops"]

  kms_key_arn = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  maintenance_window = each.value["maintenance_window"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  performance_insights_enabled = each.value["performance_insights_enabled"]

  performance_insights_kms_key_id = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  performance_insights_retention_period = each.value["performance_insights_retention_period"]

  publicly_accessible = "public" == "public" ? true : false

  rds_monitoring_interval = each.value["rds_monitoring_interval"]

  rds_monitoring_role_arn = each.value["rds_monitoring_role_arn"]

  reader_dns_name = replace("${each.key}-public-ro", "_", "-")

  regex_replace_chars = each.value["regex_replace_chars"]

  replication_source_identifier = each.value["replication_source_identifier"]

  restore_to_point_in_time = each.value["restore_to_point_in_time"]

  retention_period = each.value["retention_period"]

  s3_import = each.value["s3_import"]

  scaling_configuration = each.value["scaling_configuration"]

  security_groups = each.value["security_groups"]

  serverlessv2_scaling_configuration = each.value["serverlessv2_scaling_configuration"]

  skip_final_snapshot = each.value["skip_final_snapshot"]

  snapshot_identifier = each.value["snapshot_identifier"]

  source_region = each.value["source_region"]

  stage = lookup(each.value, "stage", local.region)

  storage_encrypted = each.value["storage_encrypted"]

  storage_type = each.value["storage_type"]

  subnet_group_name = each.value["subnet_group_name"]

  subnets = try(local.spokes_data[each.value["network_map"][local.json_key]]["public_subnet_ids"], local.public_subnet_ids)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  timeouts_configuration = each.value["timeouts_configuration"]

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  vpc_security_group_ids = each.value["vpc_security_group_ids"]

  zone_id = each.value["zone_id"]

  context = module.databases-public-context[each.key]["context"]
}

locals {
  databases_public_data = {
    for name, data in module.databases-public : name => merge(module.databases-public-context[name], data, local.databases_public_config[name], local.required_component_data, {
      for k, v in module.databases-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "databases"

      account_json_key = local.json_key

      traffic = "public"

      password = random_password.password-databases[name].result
    })
  }
}

resource "vault_kv_secret_v2" "databases-public" {
  for_each = nonsensitive(local.databases_public_data)

  mount     = "secret"
  name      = "${local.vault_path_prefix}/databases/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  databases_private_config = {
    for name, data in local.databases_base_config : name => data if data["private"]
  }
}

module "databases-private-context" {
  for_each = local.databases_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "databases-private" {
  for_each = local.databases_private_config

  source  = "cloudposse/rds-cluster/aws"
  version = "v2.3.0"

  activity_stream_enabled = each.value["activity_stream_enabled"]

  activity_stream_kms_key_id = each.value["activity_stream_kms_key_id"]

  activity_stream_mode = each.value["activity_stream_mode"]

  additional_tag_map = each.value["additional_tag_map"]

  admin_password = random_password.password-databases[each.key]["result"]

  admin_user = each.value["admin_user"]

  allocated_storage = each.value["allocated_storage"]

  allow_major_version_upgrade = each.value["allow_major_version_upgrade"]

  allowed_cidr_blocks = distinct(concat(lookup(each.value, "allowed_cidr_blocks", []), local.allowed_cidr_blocks))

  apply_immediately = each.value["apply_immediately"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  auto_minor_version_upgrade = each.value["auto_minor_version_upgrade"]

  autoscaling_enabled = coalesce(each.value["autoscaling_enabled"], local.environment != "stg" ? (each.value.cluster_size > 1 ? true : false) : false)

  autoscaling_max_capacity = each.value["autoscaling_max_capacity"]

  autoscaling_min_capacity = each.value["autoscaling_min_capacity"]

  autoscaling_policy_type = each.value["autoscaling_policy_type"]

  autoscaling_scale_in_cooldown = each.value["autoscaling_scale_in_cooldown"]

  autoscaling_scale_out_cooldown = each.value["autoscaling_scale_out_cooldown"]

  autoscaling_target_metrics = each.value["autoscaling_target_metrics"]

  autoscaling_target_value = each.value["autoscaling_target_value"]

  backtrack_window = each.value["backtrack_window"]

  backup_window = each.value["backup_window"]

  ca_cert_identifier = each.value["ca_cert_identifier"]

  cluster_dns_name = replace("${each.key}-private", "_", "-")

  cluster_family = each.value["cluster_family"]

  cluster_identifier = each.value["cluster_identifier"]

  cluster_parameters = concat(each.value["cluster_parameters"], [{
    name         = "shared_preload_libraries"
    value        = join(",", each.value["shared_preload_libraries"])
    apply_method = "pending-reboot"
  }])

  cluster_size = each.value["cluster_size"]

  cluster_type = each.value["cluster_type"]

  copy_tags_to_snapshot = each.value["copy_tags_to_snapshot"]

  db_cluster_instance_class = each.value["db_cluster_instance_class"]

  db_name = each.value["db_name"]

  db_port = each.value["db_port"]

  deletion_protection = each.value["deletion_protection"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  egress_enabled = each.value["egress_enabled"]

  enable_http_endpoint = each.value["enable_http_endpoint"]

  enabled = each.value["enabled"]

  enabled_cloudwatch_logs_exports = each.value["enabled_cloudwatch_logs_exports"]

  engine = each.value["engine"]

  engine_mode = each.value["engine_mode"]

  engine_version = each.value["engine_version"]

  enhanced_monitoring_attributes = each.value["enhanced_monitoring_attributes"]

  enhanced_monitoring_role_enabled = each.value["enhanced_monitoring_role_enabled"]

  environment = lookup(each.value, "environment", local.environment)

  global_cluster_identifier = each.value["global_cluster_identifier"]

  iam_database_authentication_enabled = each.value["iam_database_authentication_enabled"]

  iam_roles = each.value["iam_roles"]

  id_length_limit = each.value["id_length_limit"]

  instance_availability_zone = each.value["instance_availability_zone"]

  instance_parameters = concat(each.value["instance_parameters"], [{
    name         = "shared_preload_libraries"
    value        = join(",", each.value["shared_preload_libraries"])
    apply_method = "pending-reboot"
  }])

  instance_type = each.value["instance_type"]

  intra_security_group_traffic_enabled = each.value["intra_security_group_traffic_enabled"]

  iops = each.value["iops"]

  kms_key_arn = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  maintenance_window = each.value["maintenance_window"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  performance_insights_enabled = each.value["performance_insights_enabled"]

  performance_insights_kms_key_id = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  performance_insights_retention_period = each.value["performance_insights_retention_period"]

  publicly_accessible = "private" == "public" ? true : false

  rds_monitoring_interval = each.value["rds_monitoring_interval"]

  rds_monitoring_role_arn = each.value["rds_monitoring_role_arn"]

  reader_dns_name = replace("${each.key}-private-ro", "_", "-")

  regex_replace_chars = each.value["regex_replace_chars"]

  replication_source_identifier = each.value["replication_source_identifier"]

  restore_to_point_in_time = each.value["restore_to_point_in_time"]

  retention_period = each.value["retention_period"]

  s3_import = each.value["s3_import"]

  scaling_configuration = each.value["scaling_configuration"]

  security_groups = each.value["security_groups"]

  serverlessv2_scaling_configuration = each.value["serverlessv2_scaling_configuration"]

  skip_final_snapshot = each.value["skip_final_snapshot"]

  snapshot_identifier = each.value["snapshot_identifier"]

  source_region = each.value["source_region"]

  stage = lookup(each.value, "stage", local.region)

  storage_encrypted = each.value["storage_encrypted"]

  storage_type = each.value["storage_type"]

  subnet_group_name = each.value["subnet_group_name"]

  subnets = try(local.spokes_data[each.value["network_map"][local.json_key]]["private_subnet_ids"], local.private_subnet_ids)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  timeouts_configuration = each.value["timeouts_configuration"]

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  vpc_security_group_ids = each.value["vpc_security_group_ids"]

  zone_id = each.value["zone_id"]

  context = module.databases-private-context[each.key]["context"]
}

locals {
  databases_private_data = {
    for name, data in module.databases-private : name => merge(module.databases-private-context[name], data, local.databases_private_config[name], local.required_component_data, {
      for k, v in module.databases-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "databases"

      account_json_key = local.json_key

      traffic = "private"

      password = random_password.password-databases[name].result
    })
  }
}

resource "vault_kv_secret_v2" "databases-private" {
  for_each = nonsensitive(local.databases_private_data)

  mount     = "secret"
  name      = "${local.vault_path_prefix}/databases/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_databases_for_internal_use = {
    for name, _ in local.databases_base_config : name => {
      public  = lookup(local.databases_public_data, name, {})
      private = lookup(local.databases_private_data, name, {})
    }
  }

  configured_databases_both = {
    for name, data in local.configured_databases_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_databases_public_only = {
    for name, data in local.configured_databases_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_databases_private_only = {
    for name, data in local.configured_databases_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_databases = merge(flatten(concat([
    for component_name, component_data in local.databases_public_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.databases_private_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
