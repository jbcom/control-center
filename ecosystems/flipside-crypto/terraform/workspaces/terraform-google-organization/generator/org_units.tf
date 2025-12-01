module "flattened_org_units" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/flatmap"

  source_map = local.context.gws.org_units

  use_all_ancestors_in_child_keys = true

  log_file_name = "flattened_org_units.log"
}

locals {
  flattened_org_units = module.flattened_org_units.flattened_map

  # Function to determine parent key from flattened key
  org_unit_parents = {
    for org_unit_name, org_unit_config in local.flattened_org_units :
    org_unit_name => length(split("_", org_unit_name)) > 1 ? join("_", slice(split("_", org_unit_name), 0, length(split("_", org_unit_name)) - 1)) : null
  }

  # Create the Terraform resource configuration
  org_units_raw_terraform_config = {
    for org_unit_name, org_unit_config in local.flattened_org_units : org_unit_name => {
      name        = org_unit_config.name
      description = try(coalesce(org_unit_config.description), "Managed by Terraform")
    }
  }

  org_units_base_terraform_config = {
    for org_unit_name, org_unit_config in local.org_units_raw_terraform_config : org_unit_name => {
      has_parent = merge(org_unit_config, {
        parent_org_unit_id = local.org_unit_parents[org_unit_name] != null ? "$${googleworkspace_org_unit.${local.org_unit_parents[org_unit_name]}.org_unit_id}" : null
      })

      no_parent = merge(org_unit_config, {
        parent_org_unit_path = local.org_unit_parents[org_unit_name] != null ? "$${googleworkspace_org_unit.${local.org_unit_parents[org_unit_name]}.org_unit_path}" : "/"
      })
    }
  }

  org_units_terraform_config_key = {
    for org_unit_name, org_unit_config in local.org_units_base_terraform_config : org_unit_name => local.org_unit_parents[org_unit_name] != null ? "has_parent" : "no_parent"
  }

  org_units_terraform_config = {
    for org_unit_name, terraform_config_key in local.org_units_terraform_config_key : org_unit_name => local.org_units_base_terraform_config[org_unit_name][terraform_config_key]
  }
}
