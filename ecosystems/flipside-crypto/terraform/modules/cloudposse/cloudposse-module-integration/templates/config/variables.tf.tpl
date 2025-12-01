variable "infrastructure_data" {
  type = object({
%{ for module_name, generator_data in generators ~}
    ${module_name} = optional(map(object({
%{ for variable_name, variable_data in generator_data["variables"] ~}
      ${variable_name} = ${indent(6, variable_data["type"])}

%{ endfor ~}
    })))

%{ endfor ~}
  })

  description = "Infrastructure for the account"
}

variable "infrastructure_global_defaults" {
  type = any

  default = {}

  description = "Infrastructure global defaults applicable to all accounts"
}

variable "infrastructure_account_defaults" {
  type = any

  default = {}

  description = "Infrastructure defaults specific to accounts (by component FIRST, and then for each component, by account JSON key)"
}

variable "log_file_path" {
  type = string

  default = null

  description = "Log file path"
}

locals {
  log_file_path = coalesce(var.log_file_path, "$${path.root}/logs/infrastructure")
}

module "infrastructure_defaults" {
  source = "$${REL_TO_ROOT}/terraform/modules/external/defaults-merge"

  source_map = var.infrastructure_data

  defaults_file_path = "$${path.module}/defaults/infrastructure.json"

  defaults = var.infrastructure_global_defaults

  log_file_path = local.log_file_path
  log_file_name = "defaults.log"
}

locals {
  infrastructure_data = module.infrastructure_defaults.results
}

variable "extra_accounts" {
  type = any

  default = {}

  description = "Extra accounts to configure infrastructure on"
}

variable "context" {
  type = any

  description = "Context data"
}
