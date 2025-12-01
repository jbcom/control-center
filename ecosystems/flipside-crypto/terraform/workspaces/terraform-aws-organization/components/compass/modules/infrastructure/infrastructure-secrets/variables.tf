variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "doppler_project" {
  type = string

  description = "Doppler project"
}

variable "tags" {
  type = map(string)

  description = "Tags"
}

variable "context" {
  type = any

  description = "Context data"
}
