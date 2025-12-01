variable "account" {
  description = "The AWS account resource"
  type        = any
}

variable "units" {
  description = "Map of organizational units with their IDs and metadata"
  type = map(object({
    id                                = string
    name                              = string
    arn                               = string
    tags                              = map(string)
    tags_all                          = map(string)
    control_tower_organizational_unit = optional(string)
  }))
}

variable "domains" {
  description = "Domain mappings by environment"
  type        = map(string)
}

variable "caller_account_id" {
  description = "Current caller account ID for root account detection"
  type        = string
} 