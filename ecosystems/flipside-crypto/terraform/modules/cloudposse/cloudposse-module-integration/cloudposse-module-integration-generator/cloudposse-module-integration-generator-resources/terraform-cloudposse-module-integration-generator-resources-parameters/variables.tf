variable "parameters" {
  type = map(string)

  description = "Module parameters to process"
}

variable "module_config" {
  type = object({
    module_name = string

    override_module = bool

    allowlist = list(string)

    raw_denylist = list(string)

    default_resource_for_dns = bool

    data_sink = string

    use_kms_key_arn_for_id = bool

    use_security_group_rules = bool

    subdomain_suffix_keys = map(string)

    generate_password = bool
    password_length   = number

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
  })

  description = "Module config"
}