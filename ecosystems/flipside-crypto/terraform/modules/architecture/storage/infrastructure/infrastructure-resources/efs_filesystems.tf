locals {
  efs_filesystems_base_config = lookup(var.infrastructure, "efs_filesystems", {})
}

locals {
  efs_filesystems_public_config = {
    for name, data in local.efs_filesystems_base_config : name => data if data["public"]
  }
}

module "efs_filesystems-public-context" {
  for_each = local.efs_filesystems_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "efs_filesystems-public" {
  for_each = local.efs_filesystems_public_config

  source  = "cloudposse/efs/aws"
  version = "v1.4.0"

  access_points = each.value["access_points"]

  additional_tag_map = each.value["additional_tag_map"]

  allowed_cidr_blocks = ["0.0.0.0/0"]

  allowed_security_group_ids = each.value["allowed_security_group_ids"]

  associated_security_group_ids = each.value["associated_security_group_ids"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  availability_zone_name = each.value["availability_zone_name"]

  create_security_group = each.value["create_security_group"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  dns_name = replace("${each.key}-efs_filesystems-public", "_", "-")

  efs_backup_policy_enabled = each.value["efs_backup_policy_enabled"]

  enabled = each.value["enabled"]

  encrypted = each.value["encrypted"]

  environment = lookup(each.value, "environment", local.environment)

  id_length_limit = each.value["id_length_limit"]

  kms_key_id = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  mount_target_ip_address = each.value["mount_target_ip_address"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  performance_mode = each.value["performance_mode"]

  provisioned_throughput_in_mibps = each.value["provisioned_throughput_in_mibps"]

  regex_replace_chars = each.value["regex_replace_chars"]

  region = coalesce(each.value["region"], local.region)

  security_group_create_before_destroy = try(coalesce(each.value["security_group_create_before_destroy"], true), true)

  security_group_create_timeout = each.value["security_group_create_timeout"]

  security_group_delete_timeout = each.value["security_group_delete_timeout"]

  security_group_description = each.value["security_group_description"]

  security_group_name = each.value["security_group_name"]

  stage = lookup(each.value, "stage", local.region)

  subnets = try(local.spokes_data[each.value["network_map"][local.json_key]]["public_subnet_ids"], local.public_subnet_ids)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  throughput_mode = each.value["throughput_mode"]

  transition_to_ia = each.value["transition_to_ia"]

  transition_to_primary_storage_class = each.value["transition_to_primary_storage_class"]

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  zone_id = each.value["zone_id"]

  context = module.efs_filesystems-public-context[each.key]["context"]
}

locals {
  efs_filesystems_public_data = {
    for name, data in module.efs_filesystems-public : name => merge(module.efs_filesystems-public-context[name], data, local.efs_filesystems_public_config[name], local.required_component_data, {
      for k, v in module.efs_filesystems-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "efs_filesystems"

      account_json_key = local.json_key

      traffic = "public"
    })
  }
}

resource "vault_kv_secret_v2" "efs_filesystems-public" {
  for_each = local.efs_filesystems_public_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/efs_filesystems/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  efs_filesystems_private_config = {
    for name, data in local.efs_filesystems_base_config : name => data if data["private"]
  }
}

module "efs_filesystems-private-context" {
  for_each = local.efs_filesystems_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "efs_filesystems-private" {
  for_each = local.efs_filesystems_private_config

  source  = "cloudposse/efs/aws"
  version = "v1.4.0"

  access_points = each.value["access_points"]

  additional_tag_map = each.value["additional_tag_map"]

  allowed_cidr_blocks = distinct(concat(lookup(each.value, "allowed_cidr_blocks", []), local.allowed_cidr_blocks))

  allowed_security_group_ids = each.value["allowed_security_group_ids"]

  associated_security_group_ids = each.value["associated_security_group_ids"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  availability_zone_name = each.value["availability_zone_name"]

  create_security_group = each.value["create_security_group"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  dns_name = replace("${each.key}-efs_filesystems-private", "_", "-")

  efs_backup_policy_enabled = each.value["efs_backup_policy_enabled"]

  enabled = each.value["enabled"]

  encrypted = each.value["encrypted"]

  environment = lookup(each.value, "environment", local.environment)

  id_length_limit = each.value["id_length_limit"]

  kms_key_id = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  mount_target_ip_address = each.value["mount_target_ip_address"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  performance_mode = each.value["performance_mode"]

  provisioned_throughput_in_mibps = each.value["provisioned_throughput_in_mibps"]

  regex_replace_chars = each.value["regex_replace_chars"]

  region = coalesce(each.value["region"], local.region)

  security_group_create_before_destroy = try(coalesce(each.value["security_group_create_before_destroy"], true), true)

  security_group_create_timeout = each.value["security_group_create_timeout"]

  security_group_delete_timeout = each.value["security_group_delete_timeout"]

  security_group_description = each.value["security_group_description"]

  security_group_name = each.value["security_group_name"]

  stage = lookup(each.value, "stage", local.region)

  subnets = try(local.spokes_data[each.value["network_map"][local.json_key]]["private_subnet_ids"], local.private_subnet_ids)

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  throughput_mode = each.value["throughput_mode"]

  transition_to_ia = each.value["transition_to_ia"]

  transition_to_primary_storage_class = each.value["transition_to_primary_storage_class"]

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  zone_id = each.value["zone_id"]

  context = module.efs_filesystems-private-context[each.key]["context"]
}

locals {
  efs_filesystems_private_data = {
    for name, data in module.efs_filesystems-private : name => merge(module.efs_filesystems-private-context[name], data, local.efs_filesystems_private_config[name], local.required_component_data, {
      for k, v in module.efs_filesystems-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "efs_filesystems"

      account_json_key = local.json_key

      traffic = "private"
    })
  }
}

resource "vault_kv_secret_v2" "efs_filesystems-private" {
  for_each = local.efs_filesystems_private_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/efs_filesystems/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_efs_filesystems_for_internal_use = {
    for name, _ in local.efs_filesystems_base_config : name => {
      public  = lookup(local.efs_filesystems_public_data, name, {})
      private = lookup(local.efs_filesystems_private_data, name, {})
    }
  }

  configured_efs_filesystems_both = {
    for name, data in local.configured_efs_filesystems_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_efs_filesystems_public_only = {
    for name, data in local.configured_efs_filesystems_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_efs_filesystems_private_only = {
    for name, data in local.configured_efs_filesystems_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_efs_filesystems = merge(flatten(concat([
    for component_name, component_data in local.efs_filesystems_public_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.efs_filesystems_private_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
