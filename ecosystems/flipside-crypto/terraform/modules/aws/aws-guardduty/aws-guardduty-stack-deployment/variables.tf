variable "stack_name" {
  type = string

  description = "Stack name"
}

variable "stack_capabilities" {
  type = list(string)

  default = []

  description = "Stack capabilities"
}

variable "template_name" {
  type = string

  description = "Template name"
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

  description = "Records file name"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
