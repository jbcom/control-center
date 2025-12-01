locals {
  ${module_name}_base_config = lookup(var.infrastructure, "${module_name}", {})
}
%{ if generate_password ~}

resource "random_password" "password-${module_name}" {
  for_each = local.${module_name}_base_config

  length  = ${password_length}

  ${indent(2, password_options)}
}

locals {
  ${local_variable_name}_passwords = {
    for component_name, password_data in random_password.password-${module_name} : component_name => password_data["result"]
  }
}

%{ endif ~}
%{ for traffic in ["public", "private"] ~}

locals {
  ${module_name}_${traffic}_config = {
%{ if try(coalesce(infrastructure_source_key), null) != null ~}
    for name, data in local.${module_name}_base_config : name => merge(data, lookup(local.${infrastructure_source_key}_${traffic}_only, name, {})) if data["${traffic}"]
%{ else ~}
    for name, data in local.${module_name}_base_config : name => data if data["${traffic}"]
%{ endif ~}
  }
}

module "${module_name}-${traffic}-context" {
  for_each = local.${module_name}_${traffic}_config

  source  = "cloudposse/label/null"
  version = "0.25.0"

%{ for k, v in parameters["context"] ~}
  ${k} = ${indent(3, replace(v, "|TRAFFIC|", traffic))}

%{ endfor ~}
  context = var.context
}

module "${module_name}-${traffic}" {
  for_each = local.${module_name}_${traffic}_config

%{ if override_module ~}
  source = "./infrastructure-resources-overrides/${repository_name}"

%{ else ~}
  source  = "${module_source}"
  version = "${module_version}"

%{ endif ~}
%{ for k, v in parameters[traffic] ~}
  ${k} = ${indent(3, v)}

%{ endfor ~}
  context = module.${module_name}-${traffic}-context[each.key]["context"]
}

locals {
  ${module_name}_${traffic}_data = {
    for name, data in module.${module_name}-${traffic} : name => merge(module.${module_name}-${traffic}-context[name], data, local.${module_name}_${traffic}_config[name], local.required_component_data, {
      for k, v in module.${module_name}-${traffic}-context[name]["tags"] : lower(k) => v
    }, {
      short_name = name

      category = "${module_name}"

      account_json_key = local.json_key

      traffic = "${traffic}"
%{ if generate_password ~}

      password = random_password.password-${module_name}[name].result
%{ endif ~}
    })
  }
}

resource "vault_kv_secret_v2" "${module_name}-${traffic}" {
%{ if generate_password ~}
  for_each = nonsensitive(local.${module_name}_${traffic}_data)
%{ else ~}
  for_each = local.${module_name}_${traffic}_data
%{ endif ~}

  mount                      = "secret"
%{ if try(coalesce(vault_module_name), null) != null ~}
  name                       = "$${local.vault_path_prefix}/${vault_module_name}/$${each.key}"
%{ else ~}
  name                       = "$${local.vault_path_prefix}/${module_name}/$${each.key}"
%{ endif ~}
  data_json                  = jsonencode(each.value)
}
%{ endfor ~}

locals {
  ${local_variable_name}_for_internal_use = {
    for name, _ in local.${module_name}_base_config : name => {
      public   = lookup(local.${module_name}_public_data, name, {})
      private  = lookup(local.${module_name}_private_data, name, {})
    }
  }

  ${local_variable_name}_both = {
  for name, data in local.${local_variable_name}_for_internal_use : name => data if data["public"] != {} && data["private"] != {}
  }

  ${local_variable_name}_public_only = {
  for name, data in local.${local_variable_name}_for_internal_use : name => data["public"] if data["public"] != {}
  }

  ${local_variable_name}_private_only = {
  for name, data in local.${local_variable_name}_for_internal_use : name => data["private"] if data["private"] != {}
  }

  ${local_variable_name} = merge(flatten(concat([
  for component_name, component_data in local.${module_name}_public_data : {
%{ if use_component_name_as_output_id ~}
  (component_name) = component_data
%{ else ~}
  (compact([component_data["${output_id_key}"], component_data["id"], component_name])[0]) = merge(component_data, local.required_component_data)
%{ endif ~}
  }
  ], [
  for component_name, component_data in local.${module_name}_private_data : {
%{ if use_component_name_as_output_id ~}
  (component_name) = component_data
%{ else ~}
  (compact([component_data["${output_id_key}"], component_data["id"], component_name])[0]) = component_data
%{ endif ~}
  }
  ]))...)
}
