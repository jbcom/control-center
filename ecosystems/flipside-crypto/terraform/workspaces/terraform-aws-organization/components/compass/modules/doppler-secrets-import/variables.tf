variable "environment_name" {
  type = string

  description = "Environment name"
}

variable "doppler_project" {
  type = string

  description = "Doppler project"
}

variable "tags" {
  type = map(string)

  description = "Tags"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "vendors" {
  type = any

  description = "Vendor credentials from the Terraform workspace"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root from the Terraform workspace"
}
