variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "account_data" {
  type = any

  description = "Account data"
}

variable "config" {
  type = any

  description = "Configuration for each group in the environment"
}

variable "policies_config_dir" {
  type = string

  default = "config/policies"

  description = "Policies configuration directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}

variable "context" {
  type = any

  description = "Context data"
}
