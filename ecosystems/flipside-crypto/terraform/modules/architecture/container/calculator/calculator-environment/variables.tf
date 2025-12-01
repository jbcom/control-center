variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "data_key" {
  type = string

  description = "Key in the config containing the data"
}

variable "environments_key" {
  type = string

  default = "environments"

  description = "Key under the data containing environment-specific data"
}

variable "config" {
  type = any

  description = "Environment configuration"
}
