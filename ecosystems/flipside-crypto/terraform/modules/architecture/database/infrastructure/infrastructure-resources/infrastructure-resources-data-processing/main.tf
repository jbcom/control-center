locals {
  infrastructure_base_data = {
    with_children = {
      for module_name, module_data in var.infrastructure : module_name => merge(module_data, {
        children = compact(flatten([
          for child_module_name in try(module_data["child_module_names"], []) : [
            for generated_child_module_name, generated_child_module_data in try(module_data["generates"], {}) : try(generated_child_module_data["module_name"] == child_module_name ? generated_child_module_name : "", "")
          ]
        ]))
      })
    }

    without_children = var.infrastructure
  }

  num_children = length(var.children)

  infrastructure_key = local.num_children > 0 ? "with_children" : "without_children"

  infrastructure_data = local.infrastructure_base_data[local.infrastructure_key]
}