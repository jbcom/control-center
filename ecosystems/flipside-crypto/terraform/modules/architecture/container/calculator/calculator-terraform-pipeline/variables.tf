variable "pipeline_name" {
  type = string

  description = "Pipeline name"
}

variable "pipeline_config" {
  type = any

  description = "Pipeline configuration"
}

variable "base_terraform_workspace_config" {
  type = any

  description = "Base Terraform workspace configuration from the repository pipeline"
}

variable "base_terraform_workflow_config" {
  type = any

  description = "Base Terraform workflow configuration from the repository pipeline"
}

variable "base_nested_root_dir_template" {
  type = string

  description = "Base nested root directory template from the repository pipeline"
}

variable "base_nested_backend_path_prefix_template" {
  type = string

  description = "Base nested backend path prefix template from the repository pipeline"
}

variable "base_default_context_binding" {
  type = any

  description = "Base default context binding from the repository pipeline"
}

variable "context_container_config_jmes_path" {
  type = string

  default = null

  description = "JMES path for retrieving container configuration from the context object. Leading dots will be removed. If null will assume container configuration is at the root level."
}

variable "container_modules_root" {
  type = string

  default = "git@github.com:FlipsideCrypto/gitops.git/"

  description = "Terraform container modules root"
}

variable "container_modules_path" {
  type = string

  default = "terraform/modules/architecture/container"

  description = "Terraform container modules path"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}