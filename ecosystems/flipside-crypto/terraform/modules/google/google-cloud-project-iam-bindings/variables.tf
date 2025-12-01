variable "project_id" {
  description = "The project ID to apply the org policies and IAM roles."
  type        = string
}

variable "org_id" {
  description = "The organization ID."
  type        = string
}

variable "boolean_constraints" {
  description = "Map of boolean org policies to enforce."
  type        = map(bool)
}

variable "list_constraints" {
  description = "Map of list org policies to enforce."
  type = map(object({
    enforcement = optional(bool, false)
    allow       = optional(list(string), []) # Default to empty list
    deny        = optional(list(string), []) # Default to empty list
  }))
}

variable "roles" {
  description = "List of IAM roles to assign to the service account."
  type        = list(string)
}

variable "service_account_identifier" {
  description = "Service account to apply the roles to."
  type        = string
}