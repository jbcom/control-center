variable "role_name" {
  type = string

  description = "Role name"
}

variable "enabled" {
  type = bool

  default = true

  description = "Whether the role is enabled or not"
}

variable "tags" {
  type = any

  description = "Context data"
}