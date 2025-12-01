variable "config" {
  type = map(map(object({
    accounts = list(string)
  })))

  description = "Share configuration by infrastructure category, asset name, and asset share target accounts"
}

variable "infrastructure" {
  type = any

  description = "Infrastructure data for the account"
}

variable "context" {
  type = any

  description = "Context data"
}
