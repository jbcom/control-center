locals {
  s3_buckets_base_config = lookup(var.infrastructure, "s3_buckets", {})
}

locals {
  s3_buckets_public_config = {
    for name, data in local.s3_buckets_base_config : name => data if data["public"]
  }
}

module "s3_buckets-public-context" {
  for_each = local.s3_buckets_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "s3_buckets-public" {
  for_each = local.s3_buckets_public_config

  source  = "cloudposse/s3-bucket/aws"
  version = "v4.10.0"

  access_key_enabled = each.value["access_key_enabled"]

  acl = each.value["acl"]

  additional_tag_map = each.value["additional_tag_map"]

  allow_encrypted_uploads_only = each.value["allow_encrypted_uploads_only"]

  allow_ssl_requests_only = each.value["allow_ssl_requests_only"]

  allowed_bucket_actions = each.value["allowed_bucket_actions"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  block_public_acls = coalesce(each.value["block_public_acls"], "public" == "private")

  block_public_policy = coalesce(each.value["block_public_policy"], "public" == "private")

  bucket_key_enabled = each.value["bucket_key_enabled"]

  bucket_name = each.value["bucket_name"]

  cors_configuration = each.value["cors_configuration"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  enabled = each.value["managed"] ? each.value["enabled"] : false

  environment = lookup(each.value, "environment", local.environment)

  force_destroy = each.value["force_destroy"]

  grants = each.value["grants"]

  id_length_limit = each.value["id_length_limit"]

  ignore_public_acls = coalesce(each.value["ignore_public_acls"], "public" == "private")

  kms_master_key_arn = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  logging = lookup(each.value, "logging", {
    bucket_name = local.default_access_logs_bucket_name
    prefix      = "logs/${each.key}"
  })

  name = each.value["name"]

  namespace = each.value["namespace"]

  object_lock_configuration = each.value["object_lock_configuration"]

  privileged_principal_actions = each.value["privileged_principal_actions"]

  privileged_principal_arns = each.value["privileged_principal_arns"]

  regex_replace_chars = each.value["regex_replace_chars"]

  restrict_public_buckets = coalesce(each.value["restrict_public_buckets"], "public" == "private")

  s3_object_ownership = each.value["s3_object_ownership"]

  s3_replica_bucket_arn = each.value["s3_replica_bucket_arn"]

  s3_replication_enabled = each.value["s3_replication_enabled"]

  s3_replication_permissions_boundary_arn = each.value["s3_replication_permissions_boundary_arn"]

  s3_replication_rules = each.value["s3_replication_rules"]

  s3_replication_source_roles = each.value["s3_replication_source_roles"]

  source_policy_documents = each.value["source_policy_documents"]

  sse_algorithm = each.value["sse_algorithm"]

  ssm_base_path = each.value["ssm_base_path"]

  stage = lookup(each.value, "stage", local.region)

  store_access_key_in_ssm = each.value["store_access_key_in_ssm"]

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  transfer_acceleration_enabled = each.value["transfer_acceleration_enabled"]

  user_enabled = each.value["user_enabled"]

  user_permissions_boundary_arn = each.value["user_permissions_boundary_arn"]

  versioning_enabled = each.value["versioning_enabled"] ? true : (each.value["max_days"] > 0 || each.value["max_noncurrent_days"] > 0 || each.value["transition_after"] > 0 || each.value["noncurrent_transition_after"] > 0)

  website_configuration = each.value["website_configuration"]

  website_redirect_all_requests_to = each.value["website_redirect_all_requests_to"]

  context = module.s3_buckets-public-context[each.key]["context"]
}

locals {
  s3_buckets_public_data = {
    for name, data in module.s3_buckets-public : name => merge(module.s3_buckets-public-context[name], data, local.s3_buckets_public_config[name], local.required_component_data, {
      for k, v in module.s3_buckets-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "s3_buckets"

      account_json_key = local.json_key

      traffic = "public"
    })
  }
}

resource "vault_kv_secret_v2" "s3_buckets-public" {
  for_each = local.s3_buckets_public_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/s3_buckets/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  s3_buckets_private_config = {
    for name, data in local.s3_buckets_base_config : name => data if data["private"]
  }
}

module "s3_buckets-private-context" {
  for_each = local.s3_buckets_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "s3_buckets-private" {
  for_each = local.s3_buckets_private_config

  source  = "cloudposse/s3-bucket/aws"
  version = "v4.10.0"

  access_key_enabled = each.value["access_key_enabled"]

  acl = each.value["acl"]

  additional_tag_map = each.value["additional_tag_map"]

  allow_encrypted_uploads_only = each.value["allow_encrypted_uploads_only"]

  allow_ssl_requests_only = each.value["allow_ssl_requests_only"]

  allowed_bucket_actions = each.value["allowed_bucket_actions"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  block_public_acls = coalesce(each.value["block_public_acls"], "private" == "private")

  block_public_policy = coalesce(each.value["block_public_policy"], "private" == "private")

  bucket_key_enabled = each.value["bucket_key_enabled"]

  bucket_name = each.value["bucket_name"]

  cors_configuration = each.value["cors_configuration"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  enabled = each.value["managed"] ? each.value["enabled"] : false

  environment = lookup(each.value, "environment", local.environment)

  force_destroy = each.value["force_destroy"]

  grants = each.value["grants"]

  id_length_limit = each.value["id_length_limit"]

  ignore_public_acls = coalesce(each.value["ignore_public_acls"], "private" == "private")

  kms_master_key_arn = try(coalesce(each.value["kms_key_arn"], local.kms_key_arn), local.kms_key_arn)

  label_order = each.value["label_order"]

  logging = lookup(each.value, "logging", {
    bucket_name = local.default_access_logs_bucket_name
    prefix      = "logs/${each.key}"
  })

  name = each.value["name"]

  namespace = each.value["namespace"]

  object_lock_configuration = each.value["object_lock_configuration"]

  privileged_principal_actions = each.value["privileged_principal_actions"]

  privileged_principal_arns = each.value["privileged_principal_arns"]

  regex_replace_chars = each.value["regex_replace_chars"]

  restrict_public_buckets = coalesce(each.value["restrict_public_buckets"], "private" == "private")

  s3_object_ownership = each.value["s3_object_ownership"]

  s3_replica_bucket_arn = each.value["s3_replica_bucket_arn"]

  s3_replication_enabled = each.value["s3_replication_enabled"]

  s3_replication_permissions_boundary_arn = each.value["s3_replication_permissions_boundary_arn"]

  s3_replication_rules = each.value["s3_replication_rules"]

  s3_replication_source_roles = each.value["s3_replication_source_roles"]

  source_policy_documents = each.value["source_policy_documents"]

  sse_algorithm = each.value["sse_algorithm"]

  ssm_base_path = each.value["ssm_base_path"]

  stage = lookup(each.value, "stage", local.region)

  store_access_key_in_ssm = each.value["store_access_key_in_ssm"]

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  transfer_acceleration_enabled = each.value["transfer_acceleration_enabled"]

  user_enabled = each.value["user_enabled"]

  user_permissions_boundary_arn = each.value["user_permissions_boundary_arn"]

  versioning_enabled = each.value["versioning_enabled"] ? true : (each.value["max_days"] > 0 || each.value["max_noncurrent_days"] > 0 || each.value["transition_after"] > 0 || each.value["noncurrent_transition_after"] > 0)

  website_configuration = each.value["website_configuration"]

  website_redirect_all_requests_to = each.value["website_redirect_all_requests_to"]

  context = module.s3_buckets-private-context[each.key]["context"]
}

locals {
  s3_buckets_private_data = {
    for name, data in module.s3_buckets-private : name => merge(module.s3_buckets-private-context[name], data, local.s3_buckets_private_config[name], local.required_component_data, {
      for k, v in module.s3_buckets-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "s3_buckets"

      account_json_key = local.json_key

      traffic = "private"
    })
  }
}

resource "vault_kv_secret_v2" "s3_buckets-private" {
  for_each = local.s3_buckets_private_data

  mount     = "secret"
  name      = "${local.vault_path_prefix}/s3_buckets/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_s3_buckets_for_internal_use = {
    for name, _ in local.s3_buckets_base_config : name => {
      public  = lookup(local.s3_buckets_public_data, name, {})
      private = lookup(local.s3_buckets_private_data, name, {})
    }
  }

  configured_s3_buckets_both = {
    for name, data in local.configured_s3_buckets_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_s3_buckets_public_only = {
    for name, data in local.configured_s3_buckets_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_s3_buckets_private_only = {
    for name, data in local.configured_s3_buckets_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_s3_buckets = merge(flatten(concat([
    for component_name, component_data in local.s3_buckets_public_data : {
      (compact([component_data["bucket_id"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.s3_buckets_private_data : {
      (compact([component_data["bucket_id"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
