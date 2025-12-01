locals {
  dynamodb_tables_base_config = lookup(var.infrastructure, "dynamodb_tables", {})
}

locals {
  dynamodb_tables_public_config = {
    for name, data in local.dynamodb_tables_base_config : name => data if data["public"]
  }
}

module "dynamodb_tables-public-context" {
  for_each = local.dynamodb_tables_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "dynamodb_tables-public" {
  for_each = local.dynamodb_tables_public_config

  source  = "cloudposse/dynamodb/aws"
  version = "v0.37.0"

  additional_tag_map = each.value["additional_tag_map"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  autoscale_max_read_capacity = each.value["autoscale_max_read_capacity"]

  autoscale_max_write_capacity = each.value["autoscale_max_write_capacity"]

  autoscale_min_read_capacity = each.value["autoscale_min_read_capacity"]

  autoscale_min_write_capacity = each.value["autoscale_min_write_capacity"]

  autoscale_read_target = each.value["autoscale_read_target"]

  autoscale_write_target = each.value["autoscale_write_target"]

  autoscaler_attributes = each.value["autoscaler_attributes"]

  autoscaler_tags = each.value["autoscaler_tags"]

  billing_mode = each.value["billing_mode"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  dynamodb_attributes = each.value["dynamodb_attributes"]

  enable_autoscaler = each.value["enable_autoscaler"]

  enable_encryption = each.value["enable_encryption"]

  enable_point_in_time_recovery = each.value["enable_point_in_time_recovery"]

  enable_streams = each.value["enable_streams"]

  enabled = each.value["enabled"]

  environment = lookup(each.value, "environment", local.environment)

  global_secondary_index_map = each.value["global_secondary_index_map"]

  hash_key = each.value["hash_key"]

  hash_key_type = each.value["hash_key_type"]

  id_length_limit = each.value["id_length_limit"]

  label_order = each.value["label_order"]

  local_secondary_index_map = each.value["local_secondary_index_map"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  range_key = each.value["range_key"]

  range_key_type = each.value["range_key_type"]

  regex_replace_chars = each.value["regex_replace_chars"]

  replicas = each.value["replicas"]

  server_side_encryption_kms_key_arn = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  stage = lookup(each.value, "stage", local.region)

  stream_view_type = each.value["stream_view_type"]

  table_class = each.value["table_class"]

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tags_enabled = each.value["tags_enabled"]

  tenant = each.value["tenant"]

  ttl_attribute = each.value["ttl_attribute"]

  ttl_enabled = each.value["ttl_enabled"]

  context = module.dynamodb_tables-public-context[each.key]["context"]
}

locals {
  dynamodb_tables_public_data = {
    for name, data in module.dynamodb_tables-public : name => merge(module.dynamodb_tables-public-context[name], data, local.dynamodb_tables_public_config[name], local.required_component_data, {
      for k, v in module.dynamodb_tables-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "dynamodb_tables"

      account_json_key = local.json_key

      traffic = "public"
    })
  }
}

resource "vault_kv_secret_v2" "dynamodb_tables-public" {
  for_each = local.dynamodb_tables_public_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/dynamodb_tables/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  dynamodb_tables_private_config = {
    for name, data in local.dynamodb_tables_base_config : name => data if data["private"]
  }
}

module "dynamodb_tables-private-context" {
  for_each = local.dynamodb_tables_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "dynamodb_tables-private" {
  for_each = local.dynamodb_tables_private_config

  source  = "cloudposse/dynamodb/aws"
  version = "v0.37.0"

  additional_tag_map = each.value["additional_tag_map"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  autoscale_max_read_capacity = each.value["autoscale_max_read_capacity"]

  autoscale_max_write_capacity = each.value["autoscale_max_write_capacity"]

  autoscale_min_read_capacity = each.value["autoscale_min_read_capacity"]

  autoscale_min_write_capacity = each.value["autoscale_min_write_capacity"]

  autoscale_read_target = each.value["autoscale_read_target"]

  autoscale_write_target = each.value["autoscale_write_target"]

  autoscaler_attributes = each.value["autoscaler_attributes"]

  autoscaler_tags = each.value["autoscaler_tags"]

  billing_mode = each.value["billing_mode"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  dynamodb_attributes = each.value["dynamodb_attributes"]

  enable_autoscaler = each.value["enable_autoscaler"]

  enable_encryption = each.value["enable_encryption"]

  enable_point_in_time_recovery = each.value["enable_point_in_time_recovery"]

  enable_streams = each.value["enable_streams"]

  enabled = each.value["enabled"]

  environment = lookup(each.value, "environment", local.environment)

  global_secondary_index_map = each.value["global_secondary_index_map"]

  hash_key = each.value["hash_key"]

  hash_key_type = each.value["hash_key_type"]

  id_length_limit = each.value["id_length_limit"]

  label_order = each.value["label_order"]

  local_secondary_index_map = each.value["local_secondary_index_map"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  range_key = each.value["range_key"]

  range_key_type = each.value["range_key_type"]

  regex_replace_chars = each.value["regex_replace_chars"]

  replicas = each.value["replicas"]

  server_side_encryption_kms_key_arn = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  stage = lookup(each.value, "stage", local.region)

  stream_view_type = each.value["stream_view_type"]

  table_class = each.value["table_class"]

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tags_enabled = each.value["tags_enabled"]

  tenant = each.value["tenant"]

  ttl_attribute = each.value["ttl_attribute"]

  ttl_enabled = each.value["ttl_enabled"]

  context = module.dynamodb_tables-private-context[each.key]["context"]
}

locals {
  dynamodb_tables_private_data = {
    for name, data in module.dynamodb_tables-private : name => merge(module.dynamodb_tables-private-context[name], data, local.dynamodb_tables_private_config[name], local.required_component_data, {
      for k, v in module.dynamodb_tables-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "dynamodb_tables"

      account_json_key = local.json_key

      traffic = "private"
    })
  }
}

resource "vault_kv_secret_v2" "dynamodb_tables-private" {
  for_each = local.dynamodb_tables_private_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/dynamodb_tables/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_dynamodb_tables_for_internal_use = {
    for name, _ in local.dynamodb_tables_base_config : name => {
      public  = lookup(local.dynamodb_tables_public_data, name, {})
      private = lookup(local.dynamodb_tables_private_data, name, {})
    }
  }

  configured_dynamodb_tables_both = {
    for name, data in local.configured_dynamodb_tables_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_dynamodb_tables_public_only = {
    for name, data in local.configured_dynamodb_tables_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_dynamodb_tables_private_only = {
    for name, data in local.configured_dynamodb_tables_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_dynamodb_tables = merge(flatten(concat([
    for component_name, component_data in local.dynamodb_tables_public_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.dynamodb_tables_private_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
