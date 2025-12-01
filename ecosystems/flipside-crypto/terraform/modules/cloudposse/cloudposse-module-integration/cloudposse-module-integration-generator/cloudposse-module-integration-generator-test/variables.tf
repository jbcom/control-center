variable "variable_name" {
  type = string

  description = "Variable name"
}

variable "variable_data" {
  type = any
  #  object({
  #    type                = string
  #    description         = string
  #    source              = string
  #    default_value       = string
  #    override_value      = string
  #    default_generator   = string
  #    parameter_generator = string
  #    internal            = bool
  #  }))

  description = "Variable data"
}