variable "category_name" {
  type = string

  default = null

  description = "Category name"
}

variable "asset_name" {
  type = string

  default = null

  description = "Asset name"
}

variable "matchers" {
  type = list(string)

  default = []

  description = "Matchers in the secret key to search for - Matches are done partially checking if the key starts with the matcher"
}

variable "expected_assets" {
  type = number

  default = 0

  description = "Expected number of found assets"
}

variable "secret_environment" {
  type = string

  default = null

  description = "Infrastructure environment. Will otherwise use the context environment."
}

variable "secret_account" {
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
