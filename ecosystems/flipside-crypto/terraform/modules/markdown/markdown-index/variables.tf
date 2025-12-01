variable "pattern" {
  type = string

  default = "**/*.md"

  description = "Pattern to use for searching for files"
}

variable "docs_dir" {
  type = string

  default = "docs"

  description = "Docs dir to generate an index for"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}