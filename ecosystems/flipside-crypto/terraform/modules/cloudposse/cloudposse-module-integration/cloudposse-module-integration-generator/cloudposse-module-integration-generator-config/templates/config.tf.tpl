locals {
  ${module_name}_allowlist = coalescelist([
%{ for json_key in account_allowlist ~}
    "${json_key}",
%{ endfor ~}
  ], keys(local.networked_accounts_data))

  ${module_name}_denylist = [
%{ for json_key in account_denylist ~}
    "${json_key}",
%{ endfor ~}
  ]
}

module "${module_name}-defaults" {
  for_each = local.infrastructure_data["${infrastructure_source_name}"]

  source = "$${REL_TO_ROOT}/terraform/modules/external/defaults-merge-multiple-cycles"

  source_map = each.value

  cycles = {
    for json_key, account_data in local.networked_accounts_data : json_key => {
      defaults = merge({
%{ for variable_name, generator in defaults ~}
        ${variable_name} = ${indent(8, tostring(generator))}

%{ endfor ~}
      }, try(var.infrastructure_account_defaults["${module_name}"][json_key], {}))

      base_data = {}

      override_data = {
%{ for variable_name, generator in overrides ~}
%{ if try(indent(8, tostring(generator)), null) != null ~}
        ${variable_name} = ${indent(8, tostring(generator))}
%{ else ~}
%{ if try(merge(generator, {}), null) != null ~}
        ${variable_name} = {
%{ for k, v in generator ~}
          ${k} = "${v}"

%{ endfor ~}
        }
%{ else ~}
        ${variable_name} = [
%{ for v in generator ~}
          "${v}",
%{ endfor ~}
        ]
%{ endif ~}
%{ endif ~}
%{ endfor ~}
      }

      required = [
%{ for variable_name in required ~}
        "${variable_name}",
%{ endfor ~}
      ]
    } if contains(local.${module_name}_allowlist, json_key) && !contains(local.${module_name}_denylist, json_key)
  }

  allow_empty_values = false

  allowlist_key = "accounts"

  defaults_file_path = "$${path.module}/defaults/${module_name}.json"

  log_file_path = "$${local.log_file_path}/${module_name}/$${each.key}"
}

locals {
  ${module_name}_config = {
  for module_name, module_data in module.${module_name}-defaults : module_name => module_data["cycles"]
  }
}