variable "module_name" {
  type = string

  description = "Module name"
}

variable "module_config" {
  type = object({
    description = string

    repository_name = string
    repository_tag  = string

    variable_files = optional(list(string), [])

    parent_module_name = optional(string, "")
    vault_module_name  = optional(string, "")

    file_name_prefix = optional(string, "")

    file_name_suffix = optional(string, "")

    override_module = optional(bool, false)

    default_resource_for_dns = optional(bool, false)

    name_generator = optional(string, "each.key")

    map_name_to = optional(list(string), ["name"])

    map_sanitized_name_to = optional(list(string), [])

    map_admin_principals_to = optional(list(string), [])

    map_kms_key_arn_to = optional(list(string), [])

    map_artifacts_bucket_arn_to = optional(list(string), [])

    generate_password = optional(bool, false)

    map_password_to = optional(list(string), [])

    data_sink = optional(string, "each.value")

    #      variables = optional(map(object({
    #        type                = optional(string)
    #        default_value       = optional(any)
    #        override_value      = optional(any)
    #        default_generator   = optional(string)
    #        parameter_generator = optional(string)
    #        internal            = optional(bool)
    #        description         = optional(string)
    #      })))

    merge_across_accounts = optional(bool, true)

    variables = optional(any, {})

    required_variable_files = optional(list(string), [
      "context.tf",
      "variables.tf",
    ])

    save_outputs_to_ssm = optional(list(string), [])

    allowlist = optional(list(string), [])
    denylist  = optional(list(string), [])

    #    generates = optional(map(object({
    #      map_outputs_to = map(string)
    #      module_config = any
    #    })))

    generates = optional(any, {})

    use_kms_key_arn_for_id = optional(bool, false)

    use_security_group_rules = optional(bool, false)

    subdomain_suffix_keys = optional(map(string), {})

    additional_security_group_rules_key      = optional(string, "additional_security_group_rules")
    allowed_cidr_blocks_key                  = optional(string, "allowed_cidr_blocks")
    allowed_security_groups_key              = optional(string, "allowed_security_groups")
    security_group_create_before_destroy_key = optional(string, "security_group_create_before_destroy")
    password_length                          = optional(number, 24)
    password_options = optional(string, <<EOT
special = false
    EOT
    )

    kms_key_id_key         = optional(string, "kms_key_id")
    kms_key_arn_key        = optional(string, "kms_key_arn")
    writer_dns_name_key    = optional(string, "")
    reader_dns_name_key    = optional(string, "")
    vpc_id_key             = optional(string, "vpc_id")
    public_subnet_ids_key  = optional(string, "public_subnet_ids")
    private_subnet_ids_key = optional(string, "private_subnet_ids")
    zone_id_key            = optional(string, "zone_id")
    zone_name_key          = optional(string, "zone_name")

    output_id_key = optional(string, "id_full")

    use_component_name_as_output_id = optional(bool, false)

    account_allowlist = optional(list(string), [])
    account_denylist  = optional(list(string), [])
  })

  description = "Module config"
}

variable "paths" {
  type = map(object({
    path        = string
    rel_to_root = string
  }))

  description = "Module paths"
}
