locals {
  module_variables_data = var.module_config.variables
}

locals {
  defaults_file_data = {
    for variable_name, variable_data in local.module_variables_data : variable_name => variable_data["default_value"]
  }

  path_data = var.module_config.paths["config"]

  local_variable_name = "${var.module_config.module_name}_config"

  default_generators_data = {
    for variable_name, variable_data in local.module_variables_data : variable_name => variable_data["default_generator"] if lookup(variable_data, "default_generator", null) != null
  }

  override_values_data = {
    for variable_name, variable_data in local.module_variables_data : variable_name => variable_data["override_value"] if lookup(variable_data, "override_value", null) != null
  }

  required_variables_data = [
    for variable_name, variable_data in local.module_variables_data : variable_name if variable_data["required"]
  ]
}

locals {
  files_data = merge({
    (local.path_data["path"]) = {
      "${local.path_data["base_file_name"]}.tf" = templatefile("${path.module}/templates/config.tf.tpl", merge(var.module_config, {
        defaults = local.default_generators_data

        overrides = local.override_values_data

        required = local.required_variables_data

        local_variable_name = local.local_variable_name

        rel_to_root = local.path_data["rel_to_root"]
      }))
    }
    }, {
    "${local.path_data["path"]}/defaults" = {
      "${local.path_data["base_file_name"]}.json" = jsonencode(local.defaults_file_data)
    }
  })

  module_config = merge(var.module_config, {
    files = local.files_data

    defaults_file = local.defaults_file_data

    locals = {
      config = local.local_variable_name
    }
  })
}