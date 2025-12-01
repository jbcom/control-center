variable "active_account" {
  type = string

  description = "Active account JSON key"
}

variable "infrastructure" {
  type = any

  description = "Infrastructure data"
}

variable "context" {
  type = any

  description = "Context data"
}