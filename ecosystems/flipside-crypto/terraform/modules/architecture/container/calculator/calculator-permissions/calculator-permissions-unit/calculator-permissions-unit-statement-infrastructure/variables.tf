variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "account_json_key" {
  type = string

  description = "Account JSON key"
}

variable "infrastructure" {
  type = list(object({
    category = string
    key      = string
    matchers = map(string)
    type     = optional(string, "")
    accounts = optional(map(string), {})
  }))

  description = "Infrastructure configuration"
}

variable "context" {
  type = any

  description = "Context data"
}
