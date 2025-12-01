variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "config" {
  type = any

  description = "Configuration for the environment"
}

variable "context" {
  type = any

  description = "Context data"
}
