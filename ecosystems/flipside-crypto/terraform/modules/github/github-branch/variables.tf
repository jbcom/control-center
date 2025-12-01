variable "repository_name" {
  type = string

  description = "Repository name"
}

variable "branch_name" {
  type = string

  description = "Branch name"
}

variable "default_branch" {
  type = bool

  default = false

  description = "Whether this branch is the default branch or not"
}