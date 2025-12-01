variable "unit_name" {
  type = string

  description = "Unit name"
}

variable "unit_config" {
  type = object({
    unit_name = optional(string)

    spoke = optional(bool, false)
  })
  description = "Unit configuration"
}

variable "parent_id" {
  type = string

  description = "Parent ID of the unit"
}

variable "tags" {
  type = map(string)

  default = {}

  description = "Tags"
}