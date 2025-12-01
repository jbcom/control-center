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

locals {
  fields = [
    "type",
    "description",
    "source",
    "default_value",
    "override_value",
    "default_generator",
    "parameter_generator",
    "internal",
  ]
}


data "assert_test" "variable-contains-field" {
  for_each = toset(local.fields)

  test  = contains(keys(var.variable_data), each.key)
  throw = "Variable: ${var.variable_name}, with data: ${jsonencode(var.variable_data)}, is missing field: ${each.key}"
}