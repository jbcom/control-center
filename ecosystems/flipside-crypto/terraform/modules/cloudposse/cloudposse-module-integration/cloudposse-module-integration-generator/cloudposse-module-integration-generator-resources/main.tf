locals {
  module_name = var.module_config.module_name

  module_variables_data = var.module_config.variables

  allowlist_data = coalescelist(var.module_config.raw_allowlist, keys(local.module_variables_data))

  local_variable_name = "configured_${var.module_config.module_name}"

  raw_module_config = merge(var.module_config, {
    local_variable_name = local.local_variable_name

    allowlist = local.allowlist_data
  })
}

module "context-parameters" {
  source = "./terraform-cloudposse-module-integration-generator-resources-parameters"

  parameters = {
    for variable_name, variable_data in local.module_variables_data : variable_name => variable_data["parameter_generator"] if !variable_data["internal"] && variable_data["source"] == "context.tf"
  }

  module_config = local.raw_module_config
}

module "parameters" {
  source = "./terraform-cloudposse-module-integration-generator-resources-parameters"

  parameters = {
    for variable_name, variable_data in local.module_variables_data : variable_name => variable_data["parameter_generator"] if !variable_data["internal"] && variable_data["source"] != "context.tf"
  }

  module_config = local.raw_module_config
}

module "parameters-funnel" {
  for_each = toset([
    "public",
    "private",
  ])

  source = "./terraform-cloudposse-module-integration-generator-resources-funnel"

  traffic_type = each.key

  parameters = module.parameters.parameters

  module_config = local.raw_module_config
}

locals {
  parameters_data = {
    for traffic_type, parameters_data in module.parameters-funnel : traffic_type => parameters_data["parameters"]
  }

  denylist_data = {
    for traffic_type, parameters_data in module.parameters-funnel : traffic_type => parameters_data["denylist"]
  }

  locals_data = merge(local.raw_module_config["locals"], {
    resource = local.local_variable_name
  })

  default_variable_generator_template = "local.${local.locals_data["resource"]}[each.key][\"%s\"]"

  variable_generator_templates = {
    lists = "[${local.default_variable_generator_template}]"
  }

  generates_data = {
    for module_name, module_data in local.raw_module_config["generates"] : "${module_name}_from_${local.module_name}" => merge(module_data, {
      module_name = lookup(module_data, "cloudposse_module", module_name)

      parent_module_name = local.module_name

      vault_module_name = module_name

      infrastructure_source_name = local.module_name
      infrastructure_source_key  = local.local_variable_name

      infrastructure_merge_key = module_name

      raw_variables = [
        lookup(module_data, "variables", {}),
        merge(flatten([
          for output_key, data_types in lookup(module_data, "map_outputs_to", {}) : [
            for type_name, input_keys in data_types : [
              for key_name in input_keys : {
                (key_name) = {
                  parameter_generator = format(lookup(local.variable_generator_templates, type_name, local.default_variable_generator_template), output_key)
                }
              }
            ]
          ]
        ])...),
        length(lookup(module_data, "disable_generation_for", [])) > 0 ? {
          enabled = {
            parameter_generator = <<EOT
!contains([
%{for traffic in lookup(module_data, "disable_generation_for", [])~}
  "${traffic}",
%{endfor~}
], "|TRAFFIC|")
EOT
          }
        } : {}
      ]
    })
  }

  base_module_config = merge(local.raw_module_config, {
    parameters = merge(local.parameters_data, {
      context = module.context-parameters.parameters
    })

    denylist = local.denylist_data
  })

  paths_data = var.module_config["paths"]

  generated_files_raw_data = {
    for file_name in fileset("${path.module}/templates", "*.tf.tpl") : trimsuffix(file_name, ".tf.tpl") => templatefile("${path.module}/templates/${file_name}", local.base_module_config)
  }

  generated_files_data = {
    for path_key, file_data in local.generated_files_raw_data : local.paths_data[path_key]["path"] => {
      "${local.paths_data[path_key]["base_file_name"]}.tf" = file_data
    }
  }
  files_data = merge(local.raw_module_config["files"], local.generated_files_data)

  module_config = merge(local.base_module_config, {
    files = local.files_data

    locals = local.locals_data

    generates = local.generates_data

    child_module_names = distinct(flatten([
      for _, module_data in local.generates_data : module_data["module_name"]
    ]))
  })
}