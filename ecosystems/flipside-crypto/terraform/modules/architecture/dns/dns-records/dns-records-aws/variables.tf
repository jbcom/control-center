variable "infrastructure" {
  type = any

  description = "Infrastructure data containing zones and certificates delineated by account JSON key"
}

variable "json_key" {
  type = string

  description = "JSON key"
}

variable "context" {
  type = any

  description = "Context data"
}