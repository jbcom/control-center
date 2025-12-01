variable "shared_data" {
  type = any

  description = "Shared data"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "records_dir" {
  type = string

  description = "Records file directory"
}

variable "records_file_name" {
  type = string

  default = null

  description = "Records file name"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
