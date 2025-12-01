variable "name" {
  description = "Name of the account"
  type        = string
}

variable "organizational_unit" {
  description = "OU to assign the account to"
  type        = string
}

variable "organizational_unit_on_delete" {
  description = "OU to move the account to on deletion"
  type        = string
  default     = "Suspended"
}

variable "close_account_on_delete" {
  description = "Whether to close the account on deletion"
  type        = bool
  default     = true
}

variable "sso" {
  description = "SSO configuration for the account"
  type = object({
    first_name = optional(string)
    last_name  = optional(string)
    email      = optional(string)
  })
  default = {}
}

variable "caller_account_id" {
  description = "Current caller account ID for root account detection"
  type        = string
}

variable "tags" {
  type = map(string)

  default = {}

  description = "Extra tags"
}

variable "context" {
  type = any

  description = "Context data"
}
