variable "source_map" {
  type        = any
  description = "Source map to merge defaults into"
}

variable "defaults_file_path" {
  type = string

  default = ""

  description = "Defaults file to use"
}

variable "cycles" {
  type = map(object({
    base_data     = any
    override_data = any
    defaults      = any
  }))

  description = <<EOT
Cycles, each consisting of the cycle name and defaults for the cycle as well as extra data to inject.
EOT
}

variable "allowlist_key" {
  type = string

  default = ""

  description = "Optional allowlist key to use for filtering the final cycles based on generated results"
}

variable "allow_empty_values" {
  type = bool

  default = true

  description = "Whether to allow empty values or fill them with their defaults, if any"
}

variable "log_file_path" {
  type        = string
  default     = "cycles"
  description = "Log file path for the merge"
}