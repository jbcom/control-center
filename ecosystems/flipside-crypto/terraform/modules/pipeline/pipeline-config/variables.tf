variable "pipeline_name" {
  type = string

  description = "Pipeline name"
}

variable "config" {
  type = any

  description = "Repository config"
}

variable "terraform_backend" {
  type = any

  description = "Terraform backend data"
}

variable "context" {
  type = any

  description = "Context data"
}
