variable "default_context_binding" {
  type = any

  description = "Default context binding"
}

variable "networking_context_bindings" {
  type = any

  description = "Networking context bindings"
}

variable "base_terraform_workspace_config" {
  type = any

  description = "Base Terraform workspace config"
}

variable "base_terraform_workflow_config" {
  type = any

  description = "Base Terraform workflow config"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}