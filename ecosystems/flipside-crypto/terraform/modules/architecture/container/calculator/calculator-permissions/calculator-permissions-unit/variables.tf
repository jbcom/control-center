variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "account_data" {
  type = any

  description = "Account data"
}

variable "permissions" {
  type = object({
    source_policy_documents   = optional(list(string), [])
    override_policy_documents = optional(list(string), [])

    statements = optional(map(object({
      actions   = list(string)
      effect    = optional(string, "Allow")
      resources = list(string)
      conditions = optional(list(object({
        test     = string
        values   = list(string)
        variable = string
      })), [])

      infrastructure = optional(list(object({
        category = string
        key      = string
        matchers = map(string)
        type     = optional(string, "")
        accounts = optional(map(string), {})
      })), [])
    })), {})

    policies = optional(map(object({
      AwsManaged = optional(bool, false)
    })), {})
  })

  description = "Permissions configuration"
}

variable "policies_config_dir" {
  type = string

  default = "config/containers/policies"

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
