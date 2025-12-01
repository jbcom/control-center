locals {
  opensearch_base_config = lookup(var.infrastructure, "opensearch", {})
}

resource "random_password" "password-opensearch" {
  for_each = local.opensearch_base_config

  length = 24

  min_lower   = 1
  min_upper   = 1
  min_numeric = 1
  min_special = 1
}

locals {
  configured_opensearch_passwords = {
    for component_name, password_data in random_password.password-opensearch : component_name => password_data["result"]
  }
}


locals {
  opensearch_public_config = {
    for name, data in local.opensearch_base_config : name => data if data["public"]
  }
}

module "opensearch-public-context" {
  for_each = local.opensearch_public_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "opensearch-public" {
  for_each = local.opensearch_public_config

  source  = "cloudposse/elasticsearch/aws"
  version = "v2.1.0"

  additional_tag_map = each.value["additional_tag_map"]

  advanced_options = each.value["advanced_options"]

  advanced_security_options_enabled = "public" == "public" ? true : each.value["advanced_security_options_enabled"]

  advanced_security_options_internal_user_database_enabled = "public" == "public" ? true : each.value["advanced_security_options_internal_user_database_enabled"]

  advanced_security_options_master_user_arn = each.value["advanced_security_options_master_user_arn"]

  advanced_security_options_master_user_name = each.value["advanced_security_options_master_user_name"]

  advanced_security_options_master_user_password = random_password.password-opensearch[each.key]["result"]

  allowed_cidr_blocks = ["0.0.0.0/0"]

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "public",
  ])))

  automated_snapshot_start_hour = each.value["automated_snapshot_start_hour"]

  availability_zone_count = each.value["highly_available"] ? 3 : 2

  aws_ec2_service_name = each.value["aws_ec2_service_name"]

  cognito_authentication_enabled = each.value["cognito_authentication_enabled"]

  cognito_iam_role_arn = each.value["cognito_iam_role_arn"]

  cognito_identity_pool_id = each.value["cognito_identity_pool_id"]

  cognito_user_pool_id = each.value["cognito_user_pool_id"]

  create_iam_service_linked_role = each.value["create_iam_service_linked_role"]

  custom_endpoint = each.value["custom_endpoint"]

  custom_endpoint_certificate_arn = each.value["custom_endpoint_certificate_arn"]

  custom_endpoint_enabled = each.value["custom_endpoint_enabled"]

  dedicated_master_count = each.value["highly_available"] ? 3 : 0

  dedicated_master_enabled = each.value["highly_available"] ? true : false

  dedicated_master_type = each.value["dedicated_master_type"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  dns_zone_id = each.value["dns_zone_id"]

  domain_endpoint_options_enforce_https = each.value["domain_endpoint_options_enforce_https"]

  domain_endpoint_options_tls_security_policy = each.value["domain_endpoint_options_tls_security_policy"]

  domain_hostname_enabled = each.value["domain_hostname_enabled"]

  ebs_iops = each.value["ebs_iops"]

  ebs_volume_size = each.value["ebs_volume_size"]

  ebs_volume_type = each.value["ebs_volume_type"]

  elasticsearch_subdomain_name = replace("${each.key}-opensearch-public", "_", "-")

  elasticsearch_version = each.value["elasticsearch_version"]

  enabled = each.value["enabled"]

  encrypt_at_rest_enabled = each.value["encrypt_at_rest_enabled"]

  encrypt_at_rest_kms_key_id = each.value["encrypt_at_rest_kms_key_id"]

  environment = lookup(each.value, "environment", local.environment)

  iam_actions = "public" == "public" ? [] : each.value["iam_actions"]

  iam_authorizing_role_arns = "public" == "public" ? [] : each.value["iam_authorizing_role_arns"]

  iam_role_arns = "public" == "public" ? [] : each.value["iam_role_arns"]

  iam_role_max_session_duration = each.value["iam_role_max_session_duration"]

  iam_role_permissions_boundary = each.value["iam_role_permissions_boundary"]

  id_length_limit = each.value["id_length_limit"]

  ingress_port_range_end = each.value["ingress_port_range_end"]

  ingress_port_range_start = each.value["ingress_port_range_start"]

  instance_count = each.value["instance_count"]

  instance_type = each.value["instance_type"]

  kibana_hostname_enabled = each.value["kibana_hostname_enabled"]

  kibana_subdomain_name = replace("${each.key}-opensearch-public-kibana", "_", "-")

  label_order = each.value["label_order"]

  log_publishing_application_cloudwatch_log_group_arn = each.value["log_publishing_application_cloudwatch_log_group_arn"]

  log_publishing_application_enabled = each.value["log_publishing_application_enabled"]

  log_publishing_audit_cloudwatch_log_group_arn = each.value["log_publishing_audit_cloudwatch_log_group_arn"]

  log_publishing_audit_enabled = each.value["log_publishing_audit_enabled"]

  log_publishing_index_cloudwatch_log_group_arn = each.value["log_publishing_index_cloudwatch_log_group_arn"]

  log_publishing_index_enabled = each.value["log_publishing_index_enabled"]

  log_publishing_search_cloudwatch_log_group_arn = each.value["log_publishing_search_cloudwatch_log_group_arn"]

  log_publishing_search_enabled = each.value["log_publishing_search_enabled"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  node_to_node_encryption_enabled = each.value["node_to_node_encryption_enabled"]

  regex_replace_chars = each.value["regex_replace_chars"]

  security_groups = each.value["security_groups"]

  stage = lookup(each.value, "stage", local.region)

  subnet_ids = slice(try(local.spokes_data[each.value["network_map"][local.json_key]]["private_subnet_ids"], local.private_subnet_ids), 0, each.value["instance_count"])

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  vpc_enabled = "public" == "private" ? true : false

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  warm_count = each.value["warm_count"]

  warm_enabled = each.value["warm_enabled"]

  warm_type = each.value["warm_type"]

  zone_awareness_enabled = each.value["highly_available"] ? true : false

  context = module.opensearch-public-context[each.key]["context"]
}

locals {
  opensearch_public_data = {
    for name, data in module.opensearch-public : name => merge(module.opensearch-public-context[name], data, local.opensearch_public_config[name], local.required_component_data, {
      for k, v in module.opensearch-public-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "opensearch"

      account_json_key = local.json_key

      traffic = "public"

      password = random_password.password-opensearch[name].result
    })
  }
}

resource "vault_kv_secret_v2" "opensearch-public" {
  for_each = nonsensitive(local.opensearch_public_data)

  mount     = "secret"
  name      = "${local.vault_path_prefix}/opensearch/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  opensearch_private_config = {
    for name, data in local.opensearch_base_config : name => data if data["private"]
  }
}

module "opensearch-private-context" {
  for_each = local.opensearch_private_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

  context = var.context
}

module "opensearch-private" {
  for_each = local.opensearch_private_config

  source  = "cloudposse/elasticsearch/aws"
  version = "v2.1.0"

  additional_tag_map = each.value["additional_tag_map"]

  advanced_options = each.value["advanced_options"]

  advanced_security_options_enabled = "private" == "public" ? true : each.value["advanced_security_options_enabled"]

  advanced_security_options_internal_user_database_enabled = "private" == "public" ? true : each.value["advanced_security_options_internal_user_database_enabled"]

  advanced_security_options_master_user_arn = each.value["advanced_security_options_master_user_arn"]

  advanced_security_options_master_user_name = each.value["advanced_security_options_master_user_name"]

  advanced_security_options_master_user_password = random_password.password-opensearch[each.key]["result"]

  allowed_cidr_blocks = distinct(concat(lookup(each.value, "allowed_cidr_blocks", []), local.allowed_cidr_blocks))

  attributes = distinct(flatten(concat([each.value["attributes"]], [
    "private",
  ])))

  automated_snapshot_start_hour = each.value["automated_snapshot_start_hour"]

  availability_zone_count = each.value["highly_available"] ? 3 : 2

  aws_ec2_service_name = each.value["aws_ec2_service_name"]

  cognito_authentication_enabled = each.value["cognito_authentication_enabled"]

  cognito_iam_role_arn = each.value["cognito_iam_role_arn"]

  cognito_identity_pool_id = each.value["cognito_identity_pool_id"]

  cognito_user_pool_id = each.value["cognito_user_pool_id"]

  create_iam_service_linked_role = each.value["create_iam_service_linked_role"]

  custom_endpoint = each.value["custom_endpoint"]

  custom_endpoint_certificate_arn = each.value["custom_endpoint_certificate_arn"]

  custom_endpoint_enabled = each.value["custom_endpoint_enabled"]

  dedicated_master_count = each.value["highly_available"] ? 3 : 0

  dedicated_master_enabled = each.value["highly_available"] ? true : false

  dedicated_master_type = each.value["dedicated_master_type"]

  delimiter = each.value["delimiter"]

  descriptor_formats = each.value["descriptor_formats"]

  dns_zone_id = each.value["dns_zone_id"]

  domain_endpoint_options_enforce_https = each.value["domain_endpoint_options_enforce_https"]

  domain_endpoint_options_tls_security_policy = each.value["domain_endpoint_options_tls_security_policy"]

  domain_hostname_enabled = each.value["domain_hostname_enabled"]

  ebs_iops = each.value["ebs_iops"]

  ebs_volume_size = each.value["ebs_volume_size"]

  ebs_volume_type = each.value["ebs_volume_type"]

  elasticsearch_subdomain_name = replace("${each.key}-opensearch-private", "_", "-")

  elasticsearch_version = each.value["elasticsearch_version"]

  enabled = each.value["enabled"]

  encrypt_at_rest_enabled = each.value["encrypt_at_rest_enabled"]

  encrypt_at_rest_kms_key_id = each.value["encrypt_at_rest_kms_key_id"]

  environment = lookup(each.value, "environment", local.environment)

  iam_actions = "private" == "public" ? [] : each.value["iam_actions"]

  iam_authorizing_role_arns = "private" == "public" ? [] : each.value["iam_authorizing_role_arns"]

  iam_role_arns = "private" == "public" ? [] : each.value["iam_role_arns"]

  iam_role_max_session_duration = each.value["iam_role_max_session_duration"]

  iam_role_permissions_boundary = each.value["iam_role_permissions_boundary"]

  id_length_limit = each.value["id_length_limit"]

  ingress_port_range_end = each.value["ingress_port_range_end"]

  ingress_port_range_start = each.value["ingress_port_range_start"]

  instance_count = each.value["instance_count"]

  instance_type = each.value["instance_type"]

  kibana_hostname_enabled = each.value["kibana_hostname_enabled"]

  kibana_subdomain_name = replace("${each.key}-opensearch-private-kibana", "_", "-")

  label_order = each.value["label_order"]

  log_publishing_application_cloudwatch_log_group_arn = each.value["log_publishing_application_cloudwatch_log_group_arn"]

  log_publishing_application_enabled = each.value["log_publishing_application_enabled"]

  log_publishing_audit_cloudwatch_log_group_arn = each.value["log_publishing_audit_cloudwatch_log_group_arn"]

  log_publishing_audit_enabled = each.value["log_publishing_audit_enabled"]

  log_publishing_index_cloudwatch_log_group_arn = each.value["log_publishing_index_cloudwatch_log_group_arn"]

  log_publishing_index_enabled = each.value["log_publishing_index_enabled"]

  log_publishing_search_cloudwatch_log_group_arn = each.value["log_publishing_search_cloudwatch_log_group_arn"]

  log_publishing_search_enabled = each.value["log_publishing_search_enabled"]

  name = each.value["name"]

  namespace = each.value["namespace"]

  node_to_node_encryption_enabled = each.value["node_to_node_encryption_enabled"]

  regex_replace_chars = each.value["regex_replace_chars"]

  security_groups = each.value["security_groups"]

  stage = lookup(each.value, "stage", local.region)

  subnet_ids = slice(try(local.spokes_data[each.value["network_map"][local.json_key]]["private_subnet_ids"], local.private_subnet_ids), 0, each.value["instance_count"])

  tags = { for k, v in merge(local.tags, lookup(each.value, "tags", {})) : k => v if k != "Name" }

  tenant = each.value["tenant"]

  vpc_enabled = "private" == "private" ? true : false

  vpc_id = try(local.spokes_data[each.value["network_map"][local.json_key]]["vpc_id"], local.vpc_id)

  warm_count = each.value["warm_count"]

  warm_enabled = each.value["warm_enabled"]

  warm_type = each.value["warm_type"]

  zone_awareness_enabled = each.value["highly_available"] ? true : false

  context = module.opensearch-private-context[each.key]["context"]
}

locals {
  opensearch_private_data = {
    for name, data in module.opensearch-private : name => merge(module.opensearch-private-context[name], data, local.opensearch_private_config[name], local.required_component_data, {
      for k, v in module.opensearch-private-context[name]["tags"] : lower(k) => v
      }, {
      short_name = name

      category = "opensearch"

      account_json_key = local.json_key

      traffic = "private"

      password = random_password.password-opensearch[name].result
    })
  }
}

resource "vault_kv_secret_v2" "opensearch-private" {
  for_each = nonsensitive(local.opensearch_private_data)

  mount     = "secret"
  name      = "${local.vault_path_prefix}/opensearch/${each.key}"
  data_json = jsonencode(each.value)
}

locals {
  configured_opensearch_for_internal_use = {
    for name, _ in local.opensearch_base_config : name => {
      public  = lookup(local.opensearch_public_data, name, {})
      private = lookup(local.opensearch_private_data, name, {})
    }
  }

  configured_opensearch_both = {
    for name, data in local.configured_opensearch_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  configured_opensearch_public_only = {
    for name, data in local.configured_opensearch_for_internal_use : name => data["public"] if data["public"] != {}
  }

  configured_opensearch_private_only = {
    for name, data in local.configured_opensearch_for_internal_use : name => data["private"] if data["private"] != {}
  }

  configured_opensearch = merge(flatten(concat([
    for component_name, component_data in local.opensearch_public_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
    }
    ], [
    for component_name, component_data in local.opensearch_private_data : {
      (compact([component_data["id_full"], component_data["id"], component_name])[0]) = component_data
    }
  ]))...)
}
