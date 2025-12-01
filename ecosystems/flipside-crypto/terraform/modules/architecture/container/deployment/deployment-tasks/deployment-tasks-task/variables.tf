variable "task_name" {
  type = string

  description = "Task name"
}

variable "task_config" {
  type = any

  description = "Task config"
}

variable "repository_images" {
  type = any

  description = "Repository images"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "docs_dir" {
  type = string

  default = "docs"

  description = "Docs directory"
}


variable "github_actions_workflows_dir" {
  type = string

  default = "github-actions-workflows"

  description = "Github Actions workflows directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
