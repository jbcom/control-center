variable "title" {
  type = string

  default = null

  description = "Repository README title (defaults to the repository name)"
}

variable "description" {
  type = string

  default = "GitOps repository for configuration of infrastructure"

  description = "Repository README description"
}

variable "collapsible_index" {
  type = bool

  default = false

  description = "Whether the repository README index should be collapsible or not"
}

variable "extra_readme_configuration" {
  type = any

  default = {}

  description = "Extra configuration for the repository README"
}

variable "docs" {
  type = any

  default = {}

  description = "Docs data"
}

variable "infrastructure" {
  type = any

  description = "Infrastructure data"
}

variable "allowlist" {
  type = list(string)

  default = []

  description = "Allowlist for infrastructure categories"
}

variable "denylist" {
  type = list(string)

  default = []

  description = "Denylist for infrastructure categories"
}

variable "docs_dir" {
  type = string

  default = "docs/infrastructure"

  description = "Infrastructure docs directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
