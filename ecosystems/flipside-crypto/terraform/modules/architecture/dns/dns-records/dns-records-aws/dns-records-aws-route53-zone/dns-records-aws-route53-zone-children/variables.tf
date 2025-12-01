variable "parent_zone_id" {
  type = string

  description = "Parent zone ID"
}

variable "children" {
  type = any

  description = "Child zones"
}