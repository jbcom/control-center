locals {
  environment_variable_files = toset(formatlist("%s/%s/%s", var.rel_to_root, var.environment_variables_dir, var.config.files))
}

data "assert_test" "environment_variable_file_exists" {
  for_each = local.environment_variable_files

  test = fileexists(each.key) && try(yamldecode(file(each.key)), jsondecode(file(each.key)), null) != null

  throw = "Environment variable file ${each.key} does not exist locally or does not decode from YAML or JSON"
}

locals {
  environment_variable_file_data = merge(flatten([
    for file_path in local.environment_variable_files : [
      for k, v in try(yamldecode(file(file_path)), jsondecode(file(file_path)), {}) : {
        (k) = v
      }
    ]
  ])...)

  environment_variables_from_files = [
    for param_key, param_value in local.environment_variable_file_data : {
      name  = param_key
      value = param_value
    }
  ]

  environment_variables_from_context = [
    for param_key, context_key in var.config.context : {
      name  = param_key
      value = var.context[context_key]
    }
  ]

  environment_variables_from_inline = [
    for param_key, param_value in var.config.inline : {
      name  = param_key
      value = param_value
    }
  ]

  environment_variables_data = concat(local.environment_variables_from_files, local.environment_variables_from_context, local.environment_variables_from_inline)
}
