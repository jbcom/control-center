variable "name" {
  description = "Name of the account"
  type        = string
}

variable "email" {
  description = "Email address for the account"
  type        = string
  default     = null
}

variable "role_name" {
  description = "IAM role name for the account"
  type        = string
  default     = "OrganizationAccountAccessRole"
}

variable "parent" {
  description = "Parent organizational unit (if any)"
  type        = string
  default     = null
}

variable "iam_user_access_to_billing" {
  description = "Whether to allow IAM users access to account billing information"
  type        = string
  default     = "ALLOW"
}

variable "close_on_deletion" {
  description = "Whether to close the account on deletion"
  type        = bool
  default     = true
}

variable "create_govcloud" {
  description = "Whether to create a GovCloud account"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Extra tags for the account"
  type        = map(string)
  default     = {}
}
variable "caller_account_id" {
  description = "Current caller account ID for root account detection"
  type        = string
}

variable "context" {
  description = "Context map containing global configurations like domains"
  type        = any
}
