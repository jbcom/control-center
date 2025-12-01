variable "files" {
  type = map(map(string))

  description = "Files"
}

variable "root_dir" {
  type = string

  default = null

  description = "Root directory"
}

locals {
  root_dir = coalesce(var.root_dir, "${path.root}/${local.rel_to_root}")
}

variable "log_file_path" {
  type        = string
  default     = ""
  description = "Log file path"
}

variable "log_file_name" {
  type        = string
  default     = ""
  description = "Log file name"
}

locals {
  log_file_name = var.log_file_name != "" ? var.log_file_name : "${md5(jsonencode(local.files))}.log"
  log_file_path = var.log_file_path != "" ? var.log_file_path : "${path.root}/logs/local-files"
}