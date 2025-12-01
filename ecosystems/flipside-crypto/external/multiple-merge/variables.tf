variable "source_maps" {
  type = any

  description = "List of source maps to merge"
}

variable "reject_enumerables" {
  type = bool

  default = false

  description = "Whether to reject enumerable types from the merge leaving only primitives"
}

variable "reject_empty" {
  type = bool

  default = false

  description = "Whether to reject empty values from the merge"
}

variable "log_file_path" {
  type        = string
  default     = ""
  description = "Log file path for the merge. Defaults to logs/merges in the root module where executed."
}

variable "log_file_name" {
  type        = string
  default     = ""
  description = "Log file name for the merge. Defaults to the MD5 checksum of the source maps."
}