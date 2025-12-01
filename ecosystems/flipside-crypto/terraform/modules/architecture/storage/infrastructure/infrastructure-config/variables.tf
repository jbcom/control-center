variable "infrastructure_data" {
  type = object({
    access_logs = optional(map(object({
      access_log_bucket_name = optional(string)

      access_log_bucket_prefix = optional(string)

      account_id = optional(string)

      accounts = optional(list(string))

      acl = optional(string)

      additional_tag_map = optional(map(string))

      allow_ssl_requests_only = optional(bool)

      attributes = optional(list(string))

      bucket_name = optional(string)

      delimiter = optional(string)

      descriptor_formats = optional(any)

      enabled = optional(bool)

      environment = optional(string)

      execution_role_arn = optional(string)

      force_destroy = optional(bool)

      id_length_limit = optional(number)

      label_order = optional(list(string))

      lifecycle_configuration_rules = optional(any)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      private = optional(bool)

      public = optional(bool)

      regex_replace_chars = optional(string)

      stage = optional(string)

      tags = optional(map(string))

      tenant = optional(string)

      versioning_enabled = optional(bool)

    })))

    efs_filesystems = optional(map(object({
      access_points = optional(map(map(map(any))))

      account_id = optional(string)

      accounts = optional(list(string))

      additional_security_group_rules = optional(list(any))

      additional_tag_map = optional(map(string))

      allowed_cidr_blocks = optional(list(string))

      allowed_security_group_ids = optional(list(string))

      associated_security_group_ids = optional(list(string))

      attributes = optional(list(string))

      availability_zone_name = optional(string)

      create_security_group = optional(bool)

      datasync = optional(bool)

      datasync_access_point_id = optional(string)

      datasync_subdirectory = optional(string)

      delimiter = optional(string)

      descriptor_formats = optional(any)

      dns_name = optional(string)

      efs_backup_policy_enabled = optional(bool)

      efs_cross_account_policy_enabled = optional(bool)

      efs_filesystem_policy_enabled = optional(bool)

      enabled = optional(bool)

      encrypted = optional(bool)

      environment = optional(string)

      execution_role_arn = optional(string)

      id_length_limit = optional(number)

      kms_key_id = optional(string)

      label_order = optional(list(string))

      mount_target_ip_address = optional(string)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      performance_mode = optional(string)

      private = optional(bool)

      provisioned_throughput_in_mibps = optional(number)

      public = optional(bool)

      regex_replace_chars = optional(string)

      region = optional(string)

      security_group_create_before_destroy = optional(bool)

      security_group_create_timeout = optional(string)

      security_group_delete_timeout = optional(string)

      security_group_description = optional(string)

      security_group_name = optional(list(string))

      stage = optional(string)

      subnets = optional(list(string))

      tags = optional(map(string))

      tenant = optional(string)

      throughput_mode = optional(string)

      transition_to_ia = optional(list(string))

      transition_to_primary_storage_class = optional(list(string))

      vpc_id = optional(string)

      zone_id = optional(list(string))

    })))

    s3_buckets = optional(map(object({
      access_key_enabled = optional(bool)

      account_id = optional(string)

      accounts = optional(list(string))

      acl = optional(string)

      additional_tag_map = optional(map(string))

      allow_encrypted_uploads_only = optional(bool)

      allow_ssl_requests_only = optional(bool)

      allowed_bucket_actions = optional(list(string))

      attributes = optional(list(string))

      block_public_acls = optional(bool)

      block_public_policy = optional(bool)

      bucket_key_enabled = optional(bool)

      bucket_name = optional(string)

      cors_configuration = optional(any)

      datasync = optional(bool)

      datasync_storage_class = optional(string)

      datasync_subdirectory = optional(string)

      delimiter = optional(string)

      delivery_stream = optional(bool)

      descriptor_formats = optional(any)

      enabled = optional(bool)

      environment = optional(string)

      execution_role_arn = optional(string)

      extra_grants = optional(any)

      force_destroy = optional(bool)

      grant_organization_access = optional(bool)

      grants = optional(any)

      id_length_limit = optional(number)

      ignore_public_acls = optional(bool)

      kms_master_key_arn = optional(string)

      label_order = optional(list(string))

      logging = optional(any)

      managed = optional(bool)

      max_days = optional(number)

      max_noncurrent_days = optional(number)

      max_noncurrent_versions = optional(number)

      name = optional(string)

      namespace = optional(string)

      network_map = optional(map(string))

      noncurrent_transition_after = optional(number)

      noncurrent_transition_to = optional(string)

      object_lock_configuration = optional(any)

      private = optional(bool)

      privileged_principal_actions = optional(list(string))

      privileged_principal_arns = optional(list(map(list(string))))

      public = optional(bool)

      regex_replace_chars = optional(string)

      restrict_public_buckets = optional(bool)

      s3_object_ownership = optional(string)

      s3_replica_bucket_arn = optional(string)

      s3_replication_enabled = optional(bool)

      s3_replication_permissions_boundary_arn = optional(string)

      s3_replication_rules = optional(list(any))

      s3_replication_source_roles = optional(list(string))

      skip_grants = optional(bool)

      source_policy_documents = optional(list(string))

      sse_algorithm = optional(string)

      ssm_base_path = optional(string)

      stage = optional(string)

      store_access_key_in_ssm = optional(bool)

      tags = optional(map(string))

      tenant = optional(string)

      transfer_acceleration_enabled = optional(bool)

      transition_after = optional(number)

      transition_to = optional(string)

      user_enabled = optional(bool)

      user_permissions_boundary_arn = optional(string)

      versioning_enabled = optional(bool)

      website_configuration = optional(any)

      website_redirect_all_requests_to = optional(any)

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
