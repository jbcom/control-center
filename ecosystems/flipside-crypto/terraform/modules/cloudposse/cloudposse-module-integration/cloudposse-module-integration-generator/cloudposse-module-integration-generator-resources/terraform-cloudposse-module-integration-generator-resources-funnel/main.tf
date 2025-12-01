locals {
  module_name = var.module_config.module_name

  data_sink = var.module_config.data_sink

  unfiltered_parameters_data = {
    public = merge({
      for name, generator in var.parameters : name => replace(generator, "|TRAFFIC|", "public")
      }, {
      (var.module_config["public_subnet_ids_key"])               = "try(local.spokes_data[${local.data_sink}[\"network_map\"][local.json_key]][\"public_subnet_ids\"], local.public_subnet_ids)"
      (var.module_config["allowed_cidr_blocks_key"])             = "[\"0.0.0.0/0\"]"
      (var.module_config["additional_security_group_rules_key"]) = "local.public_security_group_rules"
      }, var.module_config["writer_dns_name_key"] != "" ? {
      (var.module_config["writer_dns_name_key"]) = var.module_config["default_resource_for_dns"] ? "replace(\"$${each.key}-public\", \"_\", \"-\")" : "replace(\"$${each.key}-${local.module_name}-public\", \"_\", \"-\")"
      } : {}, var.module_config["reader_dns_name_key"] != "" ? {
      (var.module_config["reader_dns_name_key"]) = var.module_config["default_resource_for_dns"] ? "replace(\"$${each.key}-public-ro\", \"_\", \"-\")" : "replace(\"$${each.key}-${local.module_name}-public-ro\", \"_\", \"-\")"
      } : {}, {
      for alias_key, alias_suffix in var.module_config["subdomain_suffix_keys"] : alias_key => var.module_config["default_resource_for_dns"] ? "replace(\"$${each.key}-public-${alias_suffix}\", \"_\", \"-\")" : "replace(\"$${each.key}-${local.module_name}-public-${alias_suffix}\", \"_\", \"-\")"
    })

    private = merge({
      for name, generator in var.parameters : name => replace(generator, "|TRAFFIC|", "private")
      }, {
      (var.module_config["private_subnet_ids_key"]) = "try(local.spokes_data[${local.data_sink}[\"network_map\"][local.json_key]][\"private_subnet_ids\"], local.private_subnet_ids)"
      (var.module_config["allowed_cidr_blocks_key"]) = format("distinct(concat(lookup(%s, \"%s\", []), local.allowed_cidr_blocks))",
        local.data_sink,
      var.module_config["allowed_cidr_blocks_key"])

      (var.module_config["additional_security_group_rules_key"]) = format("concat(lookup(%s, \"%s\", []), local.private_security_group_rules)",
        local.data_sink,
      var.module_config["additional_security_group_rules_key"])

      }, var.module_config["writer_dns_name_key"] != "" ? {
      (var.module_config["writer_dns_name_key"]) = var.module_config["default_resource_for_dns"] ? "replace(\"$${each.key}-private\", \"_\", \"-\")" : "replace(\"$${each.key}-${local.module_name}-private\", \"_\", \"-\")"
      } : {}, var.module_config["reader_dns_name_key"] != "" ? {
      (var.module_config["reader_dns_name_key"]) = var.module_config["default_resource_for_dns"] ? "replace(\"$${each.key}-private-ro\", \"_\", \"-\")" : "replace(\"$${each.key}-${local.module_name}-private-ro\", \"_\", \"-\")"
      } : {}, {
      for alias_key, alias_suffix in var.module_config["subdomain_suffix_keys"] : alias_key => var.module_config["default_resource_for_dns"] ? "replace(\"$${each.key}-private-${alias_suffix}\", \"_\", \"-\")" : "replace(\"$${each.key}-${local.module_name}-private-${alias_suffix}\", \"_\", \"-\")"
    })
  }

  raw_denylist_data = distinct(concat(var.module_config.raw_denylist, var.module_config.use_security_group_rules ? [
    var.module_config.allowed_cidr_blocks_key,
    var.module_config.allowed_security_groups_key,
    ] : [
    var.module_config.additional_security_group_rules_key,
  ]))

  base_denylist_data = {
    public = distinct(concat(local.raw_denylist_data, var.module_config.public_subnet_ids_key != var.module_config.private_subnet_ids_key ? [
      var.module_config.private_subnet_ids_key,
    ] : []))

    private = distinct(concat(local.raw_denylist_data, var.module_config.public_subnet_ids_key != var.module_config.private_subnet_ids_key ? [
      var.module_config.public_subnet_ids_key,
    ] : []))
  }

  denylist_data = local.base_denylist_data[var.traffic_type]

  module_parameters_data = {
    for name, value in local.unfiltered_parameters_data[var.traffic_type] : name => value if contains(var.module_config.allowlist, name) && !contains(local.denylist_data, name)
  }
}