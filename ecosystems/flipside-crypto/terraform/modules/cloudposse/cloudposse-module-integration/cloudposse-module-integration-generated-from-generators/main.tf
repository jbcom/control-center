locals {
  generated_child_module_data = merge(flatten([
    for module_name, module_data in var.modules_config : [
      for child_module_name, child_module_data in module_data["generates"] : {
        (child_module_name) = merge(var.modules_config[child_module_data["module_name"]], child_module_data, {
          module_name = child_module_name

          paths = {
            for path_name, path_data in var.modules_config[module_data["module_name"]]["paths"] : path_name => merge(path_data, {
              base_file_name = child_module_name
            })
          }

          raw_variables = flatten(concat([
            var.modules_config[child_module_data["module_name"]]["variables"],
            child_module_data["raw_variables"],
          ]))
        })
      }
    ]
  ])...)
}

module "config" {
  for_each = local.generated_child_module_data

  source = "../cloudposse-module-integration-generator/cloudposse-module-integration-generator-config"

  module_config = each.value
}

module "resources" {
  for_each = module.config

  source = "../cloudposse-module-integration-generator/cloudposse-module-integration-generator-resources"

  module_config = each.value.config
}

locals {
  modules_config_data = {
    for module_name, resources_data in module.resources : module_name => merge(resources_data["config"], {
      generates = local.generated_child_module_data[module_name]
    })
  }
}