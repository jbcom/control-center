variable "infrastructure" {
  type = any

  description = "Infrastructure data"
}

variable "docs" {
  type = any

  description = "Docs data"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
