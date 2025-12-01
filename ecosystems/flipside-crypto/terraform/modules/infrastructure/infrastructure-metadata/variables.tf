variable "category_name" {
  type = string

  description = "Category name"
}

variable "asset_name" {
  type = string

  default = null

  description = "Asset name"
}

variable "matchers" {
  type = map(string)

  default = {}

  description = "Matching fields and values to use when searching for the asset"
}

variable "data_key" {
  type = string

  default = null

  description = "Data key"
}

variable "expected_assets" {
  type = number

  default = 0

  description = "Expected number of found assets"
}

variable "infrastructure_environment" {
  type = string

  default = null

  description = "Infrastructure environment. Will otherwise use the context environment."
}

variable "infrastructure_account" {
  type = string

  default = null

  description = "Infrastructure account. Will otherwise use the JSON key of the account matching the active environment."
}

variable "account_map" {
  type = map(string)

  default = {}

  description = "Account map of environments to account JSON keys to use to lookup the JSON key of the active account"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "log_file_name" {
  type = string

  default = null

  description = "infrastructure-metadata.log"
}