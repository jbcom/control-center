locals {
  elasticache_redis_base_config = lookup(var.infrastructure, "elasticache_redis", {})
}

resource "random_password" "password-elasticache_redis" {
  for_each = local.elasticache_redis_base_config

  length = 24

  special = false

}

locals {
  configured_elasticache_redis_passwords = {
    for component_name, password_data in random_password.password-elasticache_redis : component_name => password_data["result"]
  }
}


locals {
  elasticache_redis_public_config = {
    for name, data in local.elasticache_redis_base_config : name => data if data["public"]
  }
}

module "elasticache_redis-public-context" {
  for_each = local.elasticache_redis_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "elasticache_redis-public" {
  for_each = local.elasticache_redis_public_config

  source  = "cloudposse/elasticache-redis/aws"
  version = "v2.0.0"

  additional_security_group_rules = local.public_security_group_rules

  additional_tag_map = each.value["additional_tag_map"]

  alarm_actions = each.value["alarm_actions"]

  alarm_cpu_threshold_percent = each.value["alarm_cpu_threshold_percent"]

  alarm_memory_threshold_bytes = each.value["alarm_memory_threshold_bytes"]

  allow_all_egress = each.value["allow_all_egress"]

  allowed_security_group_ids = each.value["allowed_security_group_ids"]

  apply_immediately = each.value["apply_immediately"]

  associated_security_group_ids = each.value["associated_security_group_ids"]

  at_rest_encryption_enabled = "public" == "public" ? each.value["transit_encryption_enabled"] : false

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  auth_token = each.value["transit_encryption_enabled"] == true && "public" == "public" ? random_password.password-elasticache_redis[each.key]["result"] : null

  auto_minor_version_upgrade = each.value["auto_minor_version_upgrade"]

  automatic_failover_enabled = each.value["cluster_mode_enabled"] ? true : each.value["automatic_failover_enabled"]

  availability_zones = each.value["availability_zones"]

  cloudwatch_metric_alarms_enabled = each.value["cloudwatch_metric_alarms_enabled"]

  cluster_mode_enabled = each.value["cluster_mode_enabled"]

  cluster_mode_num_node_groups = each.value["cluster_mode_num_node_groups"]

  cluster_mode_replicas_per_node_group = each.value["cluster_mode_replicas_per_node_group"]

  cluster_size = each.value["automatic_failover_enabled"] && each.value["cluster_size"] < 2 ? 2 : each.value["cluster_size"]

  create_security_group = each.value["create_security_group"]

  data_tiering_enabled = each.value["data_tiering_enabled"]

  delimiter = each.value["delimiter"]

  description = each.value["description"]

  descriptor_formats = each.value["descriptor_formats"]

  dns_subdomain = replace("${each.key}-elasticache_redis-public", "_", "-")

  elasticache_subnet_group_name = each.value["elasticache_subnet_group_name"]

  enabled = each.value["enabled"]

  engine_version = each.value["engine_version"]

  environment = lookup(each.value, "environment", local.environment)

  family = each.value["family"]

  final_snapshot_identifier = each.value["final_snapshot_identifier"]

  id_length_limit = each.value["id_length_limit"]

  instance_type = each.value["instance_type"]

  kms_key_id = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  log_delivery_configuration = each.value["log_delivery_configuration"]

  maintenance_window = each.value["maintenance_window"]

  multi_az_enabled = each.value["automatic_failover_enabled"] == false ? false : each.value["multi_az_enabled"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  notification_topic_arn = each.value["notification_topic_arn"]

  ok_actions = each.value["ok_actions"]

  parameter = each.value["parameter"]

  parameter_group_description = each.value["parameter_group_description"]

  port = each.value["port"]

  regex_replace_chars = each.value["regex_replace_chars"]

  replication_group_id = each.value["replication_group_id"]

  security_group_create_before_destroy = try(coalesce(each.value["security_group_create_before_destroy"], true), true)

  security_group_create_timeout = each.value["security_group_create_timeout"]

  security_group_delete_timeout = each.value["security_group_delete_timeout"]

  security_group_description = each.value["security_group_description"]

  security_group_name = each.value["security_group_name"]

  snapshot_arns = each.value["snapshot_arns"]

  snapshot_name = each.value["snapshot_name"]

  snapshot_retention_limit = each.value["snapshot_retention_limit"]

  snapshot_window = each.value["snapshot_window"]

  stage = lookup(each.value, "stage", local.region)

  subnets = try(local.spokes_data[each.value["network_map"][local.json_key]]["public_subnet_ids"], local.public_subnet_ids)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  transit_encryption_enabled = "public" == "public" ? each.value["transit_encryption_enabled"] : false

  user_group_ids = each.value["transit_encryption_enabled"] == true && "public" == "public" ? null : each.value["user_group_ids"]

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  zone_id = each.value["zone_id"]

  context = module.elasticache_redis-public-context[each.key]["context"]
}

locals {
  elasticache_redis_public_data = {
    for name, data in module.elasticache_redis-public : name => merge(module.elasticache_redis-public-context[name], data, local.elasticache_redis_public_config[name], local.required_component_data, {
      for k, v in module.elasticache_redis-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "elasticache_redis"

      account_json_key = local.json_key

      traffic = "public"

      password = random_password.password-elasticache_redis[name].result
    })
  }
}

resource "vault_kv_secret_v2" "elasticache_redis-public" {
  for_each = nonsensitive(local.elasticache_redis_public_data)

  mount     = "secret"
  name      = "${local.vault_path_prefix}/elasticache_redis/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  elasticache_redis_private_config = {
    for name, data in local.elasticache_redis_base_config : name => data if data["private"]
  }
}

module "elasticache_redis-private-context" {
  for_each = local.elasticache_redis_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "elasticache_redis-private" {
  for_each = local.elasticache_redis_private_config

  source  = "cloudposse/elasticache-redis/aws"
  version = "v2.0.0"

  additional_security_group_rules = concat(lookup(each.value, "additional_security_group_rules", []), local.private_security_group_rules)

  additional_tag_map = each.value["additional_tag_map"]

  alarm_actions = each.value["alarm_actions"]

  alarm_cpu_threshold_percent = each.value["alarm_cpu_threshold_percent"]

  alarm_memory_threshold_bytes = each.value["alarm_memory_threshold_bytes"]

  allow_all_egress = each.value["allow_all_egress"]

  allowed_security_group_ids = each.value["allowed_security_group_ids"]

  apply_immediately = each.value["apply_immediately"]

  associated_security_group_ids = each.value["associated_security_group_ids"]

  at_rest_encryption_enabled = "private" == "public" ? each.value["transit_encryption_enabled"] : false

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  auth_token = each.value["transit_encryption_enabled"] == true && "private" == "public" ? random_password.password-elasticache_redis[each.key]["result"] : null

  auto_minor_version_upgrade = each.value["auto_minor_version_upgrade"]

  automatic_failover_enabled = each.value["cluster_mode_enabled"] ? true : each.value["automatic_failover_enabled"]

  availability_zones = each.value["availability_zones"]

  cloudwatch_metric_alarms_enabled = each.value["cloudwatch_metric_alarms_enabled"]

  cluster_mode_enabled = each.value["cluster_mode_enabled"]

  cluster_mode_num_node_groups = each.value["cluster_mode_num_node_groups"]

  cluster_mode_replicas_per_node_group = each.value["cluster_mode_replicas_per_node_group"]

  cluster_size = each.value["automatic_failover_enabled"] && each.value["cluster_size"] < 2 ? 2 : each.value["cluster_size"]

  create_security_group = each.value["create_security_group"]

  data_tiering_enabled = each.value["data_tiering_enabled"]

  delimiter = each.value["delimiter"]

  description = each.value["description"]

  descriptor_formats = each.value["descriptor_formats"]

  dns_subdomain = replace("${each.key}-elasticache_redis-private", "_", "-")

  elasticache_subnet_group_name = each.value["elasticache_subnet_group_name"]

  enabled = each.value["enabled"]

  engine_version = each.value["engine_version"]

  environment = lookup(each.value, "environment", local.environment)

  family = each.value["family"]

  final_snapshot_identifier = each.value["final_snapshot_identifier"]

  id_length_limit = each.value["id_length_limit"]

  instance_type = each.value["instance_type"]

  kms_key_id = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  log_delivery_configuration = each.value["log_delivery_configuration"]

  maintenance_window = each.value["maintenance_window"]

  multi_az_enabled = each.value["automatic_failover_enabled"] == false ? false : each.value["multi_az_enabled"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  notification_topic_arn = each.value["notification_topic_arn"]

  ok_actions = each.value["ok_actions"]

  parameter = each.value["parameter"]

  parameter_group_description = each.value["parameter_group_description"]

  port = each.value["port"]

  regex_replace_chars = each.value["regex_replace_chars"]

  replication_group_id = each.value["replication_group_id"]

  security_group_create_before_destroy = try(coalesce(each.value["security_group_create_before_destroy"], true), true)

  security_group_create_timeout = each.value["security_group_create_timeout"]

  security_group_delete_timeout = each.value["security_group_delete_timeout"]

  security_group_description = each.value["security_group_description"]

  security_group_name = each.value["security_group_name"]

  snapshot_arns = each.value["snapshot_arns"]

  snapshot_name = each.value["snapshot_name"]

  snapshot_retention_limit = each.value["snapshot_retention_limit"]

  snapshot_window = each.value["snapshot_window"]

  stage = lookup(each.value, "stage", local.region)

  subnets = try(local.spokes_data[each.value["network_map"][local.json_key]]["private_subnet_ids"], local.private_subnet_ids)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  transit_encryption_enabled = "private" == "public" ? each.value["transit_encryption_enabled"] : false

  user_group_ids = each.value["transit_encryption_enabled"] == true && "private" == "public" ? null : each.value["user_group_ids"]

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  zone_id = each.value["zone_id"]

  context = module.elasticache_redis-private-context[each.key]["context"]
}

locals {
  elasticache_redis_private_data = {
    for name, data in module.elasticache_redis-private : name => merge(module.elasticache_redis-private-context[name], data, local.elasticache_redis_private_config[name], local.required_component_data, {
      for k, v in module.elasticache_redis-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "elasticache_redis"

      account_json_key = local.json_key

      traffic = "private"

      password = random_password.password-elasticache_redis[name].result
    })
  }
}

resource "vault_kv_secret_v2" "elasticache_redis-private" {
  for_each = nonsensitive(local.elasticache_redis_private_data)

  mount     = "secret"
  name      = "${local.vault_path_prefix}/elasticache_redis/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_elasticache_redis_for_internal_use = {
    for name, _ in local.elasticache_redis_base_config : name => {
      public  = lookup(local.elasticache_redis_public_data, name, {})
      private = lookup(local.elasticache_redis_private_data, name, {})
    }
  }

  configured_elasticache_redis_both = {
    for name, data in local.configured_elasticache_redis_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_elasticache_redis_public_only = {
    for name, data in local.configured_elasticache_redis_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_elasticache_redis_private_only = {
    for name, data in local.configured_elasticache_redis_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_elasticache_redis = merge(flatten(concat([
    for component_name, component_data in local.elasticache_redis_public_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.elasticache_redis_private_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
