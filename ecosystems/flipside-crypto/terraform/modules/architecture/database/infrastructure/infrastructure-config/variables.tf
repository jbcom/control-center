variable "infrastructure_data" {
  type = object({
    databases = optional(map(object({
      account_id = optional(string)

      accounts = optional(list(string))

      activity_stream_enabled = optional(bool)

      activity_stream_kms_key_id = optional(string)

      activity_stream_mode = optional(string)

      additional_tag_map = optional(map(string))

      admin_password = optional(string)

      admin_user = optional(string)

      allocated_storage = optional(number)

      allow_major_version_upgrade = optional(bool)

      allowed_cidr_blocks = optional(list(string))

      apply_immediately = optional(bool)

      attributes = optional(list(string))

      auto_minor_version_upgrade = optional(bool)

      autoscaling_enabled = optional(bool)

      autoscaling_max_capacity = optional(number)

      autoscaling_min_capacity = optional(number)

      autoscaling_policy_type = optional(string)

      autoscaling_scale_in_cooldown = optional(number)

      autoscaling_scale_out_cooldown = optional(number)

      autoscaling_target_metrics = optional(string)

      autoscaling_target_value = optional(number)

      backtrack_window = optional(number)

      backup_window = optional(string)

      ca_cert_identifier = optional(string)

      cluster_dns_name = optional(string)

      cluster_family = optional(string)

      cluster_identifier = optional(string)

      cluster_parameters = optional(any)

      cluster_size = optional(number)

      cluster_type = optional(string)

      copy_tags_to_snapshot = optional(bool)

      db_cluster_instance_class = optional(string)

      db_name = optional(string)

      db_port = optional(number)

      deletion_protection = optional(bool)

      delimiter = optional(string)

      descriptor_formats = optional(any)

      egress_enabled = optional(bool)

      enable_http_endpoint = optional(bool)

      enabled = optional(bool)

      enabled_cloudwatch_logs_exports = optional(list(string))

      engine = optional(string)

      engine_mode = optional(string)

      engine_version = optional(string)

      enhanced_monitoring_attributes = optional(list(string))

      enhanced_monitoring_role_enabled = optional(bool)

      environment = optional(string)

      execution_role_arn = optional(string)

      extensions = optional(list(string))

      global_cluster_identifier = optional(string)

      iam_database_authentication_enabled = optional(bool)

      iam_roles = optional(list(string))

      id_length_limit = optional(number)

      instance_availability_zone = optional(string)

      instance_parameters = optional(any)

      instance_type = optional(string)

      intra_security_group_traffic_enabled = optional(bool)

      iops = optional(number)

      kms_key_arn = optional(string)

      label_order = optional(list(string))

      maintenance_window = optional(string)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      performance_insights_enabled = optional(bool)

      performance_insights_kms_key_id = optional(string)

      performance_insights_retention_period = optional(number)

      private = optional(bool)

      public = optional(bool)

      publicly_accessible = optional(bool)

      rds_monitoring_interval = optional(number)

      rds_monitoring_role_arn = optional(string)

      reader_dns_name = optional(string)

      regex_replace_chars = optional(string)

      replication_source_identifier = optional(string)

      restore_to_point_in_time = optional(any)

      retention_period = optional(number)

      s3_import = optional(any)

      scaling_configuration = optional(any)

      security_groups = optional(list(string))

      serverlessv2_scaling_configuration = optional(any)

      shared_preload_libraries = optional(list(string))

      skip_final_snapshot = optional(bool)

      snapshot_identifier = optional(string)

      source_region = optional(string)

      stage = optional(string)

      storage_encrypted = optional(bool)

      storage_type = optional(string)

      subnet_group_name = optional(string)

      subnets = optional(list(string))

      tags = optional(map(string))

      tenant = optional(string)

      timeouts_configuration = optional(any)

      vpc_id = optional(string)

      vpc_security_group_ids = optional(list(string))

      zone_id = optional(any)

    })))

    dynamodb_tables = optional(map(object({
      account_id = optional(string)

      accounts = optional(list(string))

      additional_tag_map = optional(map(string))

      attributes = optional(list(string))

      autoscale_max_read_capacity = optional(number)

      autoscale_max_write_capacity = optional(number)

      autoscale_min_read_capacity = optional(number)

      autoscale_min_write_capacity = optional(number)

      autoscale_read_target = optional(number)

      autoscale_write_target = optional(number)

      autoscaler_attributes = optional(list(string))

      autoscaler_tags = optional(map(string))

      billing_mode = optional(string)

      delimiter = optional(string)

      descriptor_formats = optional(any)

      dynamodb_attributes = optional(any)

      enable_autoscaler = optional(bool)

      enable_encryption = optional(bool)

      enable_point_in_time_recovery = optional(bool)

      enable_streams = optional(bool)

      enabled = optional(bool)

      environment = optional(string)

      execution_role_arn = optional(string)

      global_secondary_index_map = optional(any)

      hash_key = optional(string)

      hash_key_type = optional(string)

      id_length_limit = optional(number)

      label_order = optional(list(string))

      local_secondary_index_map = optional(any)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      private = optional(bool)

      public = optional(bool)

      range_key = optional(string)

      range_key_type = optional(string)

      regex_replace_chars = optional(string)

      replicas = optional(list(string))

      server_side_encryption_kms_key_arn = optional(string)

      stage = optional(string)

      stream_view_type = optional(string)

      table_class = optional(string)

      tags = optional(map(string))

      tags_enabled = optional(bool)

      tenant = optional(string)

      ttl_attribute = optional(string)

      ttl_enabled = optional(bool)

    })))

    elasticache_redis = optional(map(object({
      account_id = optional(string)

      accounts = optional(list(string))

      additional_security_group_rules = optional(list(any))

      additional_tag_map = optional(map(string))

      alarm_actions = optional(list(string))

      alarm_cpu_threshold_percent = optional(number)

      alarm_memory_threshold_bytes = optional(number)

      allow_all_egress = optional(bool)

      allowed_security_group_ids = optional(list(string))

      apply_immediately = optional(bool)

      associated_security_group_ids = optional(list(string))

      at_rest_encryption_enabled = optional(bool)

      attributes = optional(list(string))

      auth_token = optional(string)

      auto_minor_version_upgrade = optional(bool)

      automatic_failover_enabled = optional(bool)

      availability_zones = optional(list(string))

      cloudwatch_metric_alarms_enabled = optional(bool)

      cluster_mode_enabled = optional(bool)

      cluster_mode_num_node_groups = optional(number)

      cluster_mode_replicas_per_node_group = optional(number)

      cluster_size = optional(number)

      create_security_group = optional(bool)

      data_tiering_enabled = optional(bool)

      delimiter = optional(string)

      description = optional(string)

      descriptor_formats = optional(any)

      dns_subdomain = optional(string)

      elasticache_subnet_group_name = optional(string)

      enabled = optional(bool)

      engine_version = optional(string)

      environment = optional(string)

      execution_role_arn = optional(string)

      family = optional(string)

      final_snapshot_identifier = optional(string)

      id_length_limit = optional(number)

      instance_type = optional(string)

      kms_key_id = optional(string)

      label_order = optional(list(string))

      log_delivery_configuration = optional(list(map(any)))

      maintenance_window = optional(string)

      multi_az_enabled = optional(bool)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      notification_topic_arn = optional(string)

      ok_actions = optional(list(string))

      parameter = optional(any)

      parameter_group_description = optional(string)

      port = optional(number)

      private = optional(bool)

      public = optional(bool)

      regex_replace_chars = optional(string)

      replication_group_id = optional(string)

      security_group_create_before_destroy = optional(bool)

      security_group_create_timeout = optional(string)

      security_group_delete_timeout = optional(string)

      security_group_description = optional(string)

      security_group_name = optional(list(string))

      snapshot_arns = optional(list(string))

      snapshot_name = optional(string)

      snapshot_retention_limit = optional(number)

      snapshot_window = optional(string)

      stage = optional(string)

      subnets = optional(list(string))

      tags = optional(map(string))

      tenant = optional(string)

      transit_encryption_enabled = optional(bool)

      user_group_ids = optional(list(string))

      vpc_id = optional(string)

      zone_id = optional(any)

    })))

    opensearch = optional(map(object({
      account_id = optional(string)

      accounts = optional(list(string))

      additional_tag_map = optional(map(string))

      advanced_options = optional(map(string))

      advanced_security_options_enabled = optional(bool)

      advanced_security_options_internal_user_database_enabled = optional(bool)

      advanced_security_options_master_user_arn = optional(string)

      advanced_security_options_master_user_name = optional(string)

      advanced_security_options_master_user_password = optional(string)

      allowed_cidr_blocks = optional(list(string))

      attributes = optional(list(string))

      automated_snapshot_start_hour = optional(number)

      availability_zone_count = optional(number)

      aws_ec2_service_name = optional(list(string))

      cognito_authentication_enabled = optional(bool)

      cognito_iam_role_arn = optional(string)

      cognito_identity_pool_id = optional(string)

      cognito_user_pool_id = optional(string)

      create_iam_service_linked_role = optional(bool)

      custom_endpoint = optional(string)

      custom_endpoint_certificate_arn = optional(string)

      custom_endpoint_enabled = optional(bool)

      dedicated_master_count = optional(number)

      dedicated_master_enabled = optional(bool)

      dedicated_master_type = optional(string)

      delimiter = optional(string)

      descriptor_formats = optional(any)

      dns_zone_id = optional(string)

      domain_endpoint_options_enforce_https = optional(bool)

      domain_endpoint_options_tls_security_policy = optional(string)

      domain_hostname_enabled = optional(bool)

      ebs_iops = optional(number)

      ebs_volume_size = optional(number)

      ebs_volume_type = optional(string)

      elasticsearch_subdomain_name = optional(string)

      elasticsearch_version = optional(string)

      enabled = optional(bool)

      encrypt_at_rest_enabled = optional(bool)

      encrypt_at_rest_kms_key_id = optional(string)

      environment = optional(string)

      execution_role_arn = optional(string)

      highly_available = optional(bool)

      iam_actions = optional(list(string))

      iam_authorizing_role_arns = optional(list(string))

      iam_role_arns = optional(list(string))

      iam_role_max_session_duration = optional(number)

      iam_role_permissions_boundary = optional(string)

      id_length_limit = optional(number)

      ingress_port_range_end = optional(number)

      ingress_port_range_start = optional(number)

      instance_count = optional(number)

      instance_type = optional(string)

      kibana_hostname_enabled = optional(bool)

      kibana_subdomain_name = optional(string)

      label_order = optional(list(string))

      log_publishing_application_cloudwatch_log_group_arn = optional(string)

      log_publishing_application_enabled = optional(bool)

      log_publishing_audit_cloudwatch_log_group_arn = optional(string)

      log_publishing_audit_enabled = optional(bool)

      log_publishing_index_cloudwatch_log_group_arn = optional(string)

      log_publishing_index_enabled = optional(bool)

      log_publishing_search_cloudwatch_log_group_arn = optional(string)

      log_publishing_search_enabled = optional(bool)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      node_to_node_encryption_enabled = optional(bool)

      private = optional(bool)

      public = optional(bool)

      regex_replace_chars = optional(string)

      security_groups = optional(list(string))

      stage = optional(string)

      subnet_ids = optional(list(string))

      tags = optional(map(string))

      tenant = optional(string)

      vpc_enabled = optional(bool)

      vpc_id = optional(string)

      warm_count = optional(number)

      warm_enabled = optional(bool)

      warm_type = optional(string)

      zone_awareness_enabled = optional(bool)

    })))

  })

  description = "Infrastructure for the account"
}

variable "infrastructure_global_defaults" {
  type = any

  default = {}

  description = "Infrastructure global defaults applicable to all accounts"
}

variable "infrastructure_account_defaults" {
  type = any

  default = {}

  description = "Infrastructure defaults specific to accounts (by component FIRST, and then for each component, by account JSON key)"
}

variable "log_file_path" {
  type = string

  default = null

  description = "Log file path"
}

locals {
  log_file_path = coalesce(var.log_file_path, "${path.root}/logs/infrastructure")
}

module "infrastructure_defaults" {
  source = "../../../../../../terraform/modules/external/defaults-merge"

  source_map = var.infrastructure_data

  defaults_file_path = "${path.module}/defaults/infrastructure.json"

  defaults = var.infrastructure_global_defaults

  log_file_path = local.log_file_path
  log_file_name = "defaults.log"
}

locals {
  infrastructure_data = module.infrastructure_defaults.results
}

variable "extra_accounts" {
  type = any

  default = {}

  description = "Extra accounts to configure infrastructure on"
}

variable "context" {
  type = any

  description = "Context data"
}
