variable "context" {
  type = any

  description = "Context data"
}

variable "tasks" {
  type = any

  description = "Tasks configuration"
}

variable "ecr_repository_urls" {
  type = any

  description = "ECR repository URLs map to build"
}

variable "image_tag" {
  type = string

  description = "Image tag that was built"
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
