locals {
  access_logs_base_config = lookup(var.infrastructure, "access_logs", {})
}

locals {
  access_logs_public_config = {
    for name, data in local.access_logs_base_config : name => data if data["public"]
  }
}

module "access_logs-public-context" {
  for_each = local.access_logs_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "access_logs-public" {
  for_each = local.access_logs_public_config

  source  = "cloudposse/lb-s3-bucket/aws"
  version = "v0.20.0"

  access_log_bucket_name = each.value["access_log_bucket_name"]

  access_log_bucket_prefix = each.value["access_log_bucket_prefix"]

  acl = each.value["acl"]

  additional_tag_map = each.value["additional_tag_map"]

  allow_ssl_requests_only = each.value["allow_ssl_requests_only"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  bucket_name = each.value["bucket_name"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  enabled = each.value["enabled"]

  environment = lookup(each.value, "environment", local.environment)

  force_destroy = each.value["force_destroy"]

  id_length_limit = each.value["id_length_limit"]

  label_order = each.value["label_order"]

  lifecycle_configuration_rules = each.value["lifecycle_configuration_rules"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  regex_replace_chars = each.value["regex_replace_chars"]

  stage = lookup(each.value, "stage", local.region)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  versioning_enabled = each.value["versioning_enabled"]

  context = module.access_logs-public-context[each.key]["context"]
}

locals {
  access_logs_public_data = {
    for name, data in module.access_logs-public : name => merge(module.access_logs-public-context[name], data, local.access_logs_public_config[name], local.required_component_data, {
      for k, v in module.access_logs-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "access_logs"

      account_json_key = local.json_key

      traffic = "public"
    })
  }
}

resource "vault_kv_secret_v2" "access_logs-public" {
  for_each = local.access_logs_public_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/access_logs/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  access_logs_private_config = {
    for name, data in local.access_logs_base_config : name => data if data["private"]
  }
}

module "access_logs-private-context" {
  for_each = local.access_logs_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "access_logs-private" {
  for_each = local.access_logs_private_config

  source  = "cloudposse/lb-s3-bucket/aws"
  version = "v0.20.0"

  access_log_bucket_name = each.value["access_log_bucket_name"]

  access_log_bucket_prefix = each.value["access_log_bucket_prefix"]

  acl = each.value["acl"]

  additional_tag_map = each.value["additional_tag_map"]

  allow_ssl_requests_only = each.value["allow_ssl_requests_only"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  bucket_name = each.value["bucket_name"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  enabled = each.value["enabled"]

  environment = lookup(each.value, "environment", local.environment)

  force_destroy = each.value["force_destroy"]

  id_length_limit = each.value["id_length_limit"]

  label_order = each.value["label_order"]

  lifecycle_configuration_rules = each.value["lifecycle_configuration_rules"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  regex_replace_chars = each.value["regex_replace_chars"]

  stage = lookup(each.value, "stage", local.region)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  versioning_enabled = each.value["versioning_enabled"]

  context = module.access_logs-private-context[each.key]["context"]
}

locals {
  access_logs_private_data = {
    for name, data in module.access_logs-private : name => merge(module.access_logs-private-context[name], data, local.access_logs_private_config[name], local.required_component_data, {
      for k, v in module.access_logs-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "access_logs"

      account_json_key = local.json_key

      traffic = "private"
    })
  }
}

resource "vault_kv_secret_v2" "access_logs-private" {
  for_each = local.access_logs_private_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/access_logs/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_access_logs_for_internal_use = {
    for name, _ in local.access_logs_base_config : name => {
      public  = lookup(local.access_logs_public_data, name, {})
      private = lookup(local.access_logs_private_data, name, {})
    }
  }

  configured_access_logs_both = {
    for name, data in local.configured_access_logs_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_access_logs_public_only = {
    for name, data in local.configured_access_logs_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_access_logs_private_only = {
    for name, data in local.configured_access_logs_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_access_logs = merge(flatten(concat([
    for component_name, component_data in local.access_logs_public_data : {
      (compact([component_data["bucket_id"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.access_logs_private_data : {
      (compact([component_data["bucket_id"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
