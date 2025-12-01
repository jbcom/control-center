locals {
  # Default Control Tower configuration
  default_control_tower = {
    landing_zone = {
      version          = "3.3"
      governed_regions = ["us-east-1"]
      centralized_logging = {
        enabled = true
        configurations = {
          logging_bucket = {
            retention_days = 365
          }
          access_logging_bucket = {
            retention_days = 3650
          }
        }
      }
      access_management = {
        enabled = true
      }
    }
    controls             = {}
    controls_with_params = {}
  }

  # Merge user-provided Control Tower configuration with defaults
  processed_control_tower = {
    landing_zone = merge(
      local.default_control_tower.landing_zone,
      try(local.context.control_tower.landing_zone, {})
    )
    controls             = try(local.context.control_tower.controls, {})
    controls_with_params = try(local.context.control_tower.controls_with_params, {})
  }

  # Extract org structure units from the YAML
  org_structure_units = try(local.context.control_tower.landing_zone.organization_structure, {})

  # Process each unit to add the name from units config
  processed_organization_structure = {
    for unit_key, unit_config in local.org_structure_units : unit_key => {
      name = try(unit_config.landing_zone_name, local.units[unit_config.unit_key].name)
    }
  }

  # Process Control Tower controls
  # Only include control name and target OU name at the generator level
  # ID lookups will be done in the organization workspace
  processed_controls = merge([
    for control_name, control_config in try(local.context.control_tower.controls, {}) : {
      for target_ou in try(control_config.target_ous, []) :
      "${control_name}:${target_ou}" => {
        control_name = control_name
        target_ou    = target_ou
      }
    }
  ]...)

  # Process Control Tower controls with parameters
  # Only include control name, target OU name, and parameters at the generator level
  # ID lookups will be done in the organization workspace
  processed_controls_with_params = merge([
    for control_name, control_config in try(local.context.control_tower.controls_with_params, {}) : {
      for target_ou in try(control_config.target_ous, []) :
      "${control_name}:${target_ou}" => {
        control_name = control_name
        target_ou    = target_ou
        parameters   = control_config.parameters
      }
    }
  ]...)

  # Update processed_control_tower with the processed organizational structure and controls
  final_control_tower = merge(local.processed_control_tower, {
    organization_structure         = local.processed_organization_structure,
    processed_controls             = local.processed_controls,
    processed_controls_with_params = local.processed_controls_with_params
  })
}