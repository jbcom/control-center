variable "source_map" {
  type        = any
  description = "Source map to merge defaults into"
}

variable "defaults_file_path" {
  type = string

  default = ""

  description = "Defaults file to use"
}

variable "defaults" {
  type = any

  default = {}

  description = <<EOT
Defaults to use.
Follows the same rules as passing a defaults file, and takes precedent over one if both are passed
EOT
}

variable "base" {
  type = any

  default = {}

  description = "Extra data to merge the results onto overriding any keys in the base data"
}

variable "overrides" {
  type = any

  default = {}

  description = "Extra data to inject into the results overriding any existing matching keys"
}

variable "allow_empty_values" {
  type = bool

  default = true

  description = "Whether to allow empty values or fill them with their defaults, if any"
}

variable "allowlist_key" {
  type = string

  default = ""

  description = "Optional allowlist key in the final results that must contain a specific value"
}

variable "allowlist_value" {
  type = string

  default = ""

  description = "Optional specific value in the final results that must be within the specified allowlist key"
}

variable "log_file_path" {
  type        = string
  default     = ""
  description = "Log file path for the merge. Defaults to logs/merges in the root module where executed."
}

variable "log_file_name" {
  type        = string
  default     = ""
  description = "Log file name for the merge. Defaults to MD5 hashes for the source map and defaults."
}