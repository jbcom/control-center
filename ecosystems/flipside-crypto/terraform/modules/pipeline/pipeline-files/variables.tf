variable "repository_name" {
  type = string

  description = "Repository name"
}

variable "config" {
  type = any

  description = "Repository config"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}