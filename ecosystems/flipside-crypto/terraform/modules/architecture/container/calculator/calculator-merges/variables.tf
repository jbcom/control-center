variable "config" {
  type = any

  description = "Environment configuration"
}

variable "merge_config_key" {
  type = string

  default = "merges"

  description = "Merge config key"
}

variable "merge_config_dir" {
  type = string

  default = "config/containers/merges"

  description = "Merge configuration directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
