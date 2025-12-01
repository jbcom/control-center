variable "repository_name" {
  type = string

  description = "Repository name"
}

variable "read_only" {
  type = bool

  default = false

  description = "Read-only key"
}

variable "tags" {
  type = map(string)

  description = "Tags for the deploy key parameters"
}

variable "enabled" {
  type = bool

  default = true

  description = "Whether to create the deploy key or not"
}