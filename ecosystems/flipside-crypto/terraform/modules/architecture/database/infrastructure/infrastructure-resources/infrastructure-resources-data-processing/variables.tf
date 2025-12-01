variable "infrastructure" {
  type = any

  description = "Infrastructure data"
}

variable "children" {
  type = list(string)

  description = "List of children for the infrastructure"
}