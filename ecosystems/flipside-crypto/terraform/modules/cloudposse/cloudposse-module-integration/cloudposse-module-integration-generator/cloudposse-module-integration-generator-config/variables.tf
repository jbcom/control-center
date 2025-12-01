variable "module_config" {
  type = object({
    module_name = string

    parent_module_name = string
    vault_module_name  = string

    infrastructure_merge_key = string

    infrastructure_source_name = string
    infrastructure_source_key  = string

    paths = map(object({
      base_file_name = string
      path           = string
      rel_to_root    = string
    }))

    repository_name = string
    repository_tag  = string

    module_source  = string
    module_version = string

    override_module = bool

    raw_allowlist = list(string)
    raw_denylist  = list(string)

    merge_across_accounts = bool

    variables = any
    #    variables = map(object({
    #      type                = string
    #      description         = string
    #      source              = string
    #      default_value       = any
    #      override_value      = any
    #      default_generator   = string
    #      parameter_generator = string
    #      internal            = bool
    #    }))

    save_outputs_to_ssm = list(string)

    default_resource_for_dns = bool

    data_sink = string

    use_kms_key_arn_for_id = bool

    use_security_group_rules = bool

    subdomain_suffix_keys = map(string)

    generate_password = bool
    password_length   = number
    password_options  = string

    additional_security_group_rules_key      = string
    allowed_cidr_blocks_key                  = string
    allowed_security_groups_key              = string
    security_group_create_before_destroy_key = string
    kms_key_id_key                           = string
    kms_key_arn_key                          = string
    writer_dns_name_key                      = string
    reader_dns_name_key                      = string
    vpc_id_key                               = string
    public_subnet_ids_key                    = string
    private_subnet_ids_key                   = string
    zone_id_key                              = string
    zone_name_key                            = string

    output_id_key = string

    use_component_name_as_output_id = bool

    generates = any

    account_allowlist = list(string)
    account_denylist  = list(string)
  })

  description = "Module config"
}