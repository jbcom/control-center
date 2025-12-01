variable "enabled" {
  type = bool

  default = true

  description = "Whether to enable the directory or not"
}

variable "kms_key_arn" {
  type = string

  description = "KMS key ARN"
}

variable "base_dir" {
  type = string

  default = "."

  description = "Base directory"
}

variable "secrets_dir" {
  type = string

  default = "secrets"

  description = "Secrets directory"
}

variable "docs_title" {
  type = string

  default = ""

  description = "Title for the documentation - Defaults to the secrets directory name"
}

variable "docs_dir" {
  type = string

  default = "docs"

  description = "Documentation directory"
}

variable "readme_name" {
  type = string

  default = null

  description = "Readme file name"
}

variable "save_files" {
  type = bool

  default = false

  description = "Whether to save files locally"
}

variable "rel_to_root" {
  type = string

  default = ""

  description = "Relative path to the repository root"
}