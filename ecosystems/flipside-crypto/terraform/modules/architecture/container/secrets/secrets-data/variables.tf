variable "secret_manager_name_prefix" {
  type = string

  default = ""

  description = "Prefix for Secret Manager"
}

variable "config" {
  type = object({
    parameters = optional(map(string), {})

    parameters_by_path = optional(map(map(string)), {})

    secrets = optional(map(string), {})

    files = optional(list(string), [])
    data  = optional(map(string), {})

    architecture = optional(map(object({
      category = string
      key      = string
      type     = optional(string, "")
      accounts = optional(map(string), {})
    })), {})

    infrastructure = optional(map(object({
      category = string
      key      = string
      matchers = map(string)
      type     = optional(string, "")
      accounts = optional(map(string), {})
    })), {})

    trim = optional(map(object({
      prefix = optional(string, "")
      suffix = optional(string, "")
    })), {})
  })

  description = "Secrets configuration"
}

variable "secrets_dir" {
  type = string

  default = "secrets"

  description = "Secrets directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}

variable "debug_file" {
  type = string

  default = ""

  description = "Debug file"
}

variable "context" {
  type = any

  description = "Context data"
}
