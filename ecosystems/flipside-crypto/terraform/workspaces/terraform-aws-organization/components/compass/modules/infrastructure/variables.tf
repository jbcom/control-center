variable "context" {
  type = any

  description = "Context data from the Terraform workspace"
}

variable "vendors" {
  type = any

  description = "Vendor credentials from the Terraform workspace"
}

variable "grafana_api_key" {
  type = string

  sensitive = true

  description = "Grafana API key"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root from the Terraform workspace"
}

variable "records_dir" {
  type = string

  description = "Records directory"
}
