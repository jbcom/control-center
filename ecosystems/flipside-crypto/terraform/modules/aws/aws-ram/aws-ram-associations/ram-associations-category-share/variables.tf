variable "config" {
  type = map(object({
    accounts = list(string)
  }))

  description = "Share configuration by  asset name, and asset share target accounts"
}

variable "infrastructure" {
  type = any

  description = "Category infrastructure data"
}

variable "context" {
  type = any

  description = "Context data"
}
