variable "account" {
  description = "Account configuration object"
  type        = any
}

variable "caller_account_id" {
  description = "Current caller account ID for root account detection"
  type        = string
}

variable "context" {
  description = "Context map containing global configurations like domains"
  type        = any
}

variable "units" {
  description = "Map of organizational units with their IDs and metadata"
  type = map(object({
    id       = string
    name     = string
    arn      = string
    tags     = map(string)
    tags_all = map(string)
  }))
}
