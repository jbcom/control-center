variable "task_name" {
  type = string

  description = "Task name"
}

variable "deployment_config" {
  type = any

  description = "deployment config"
}

variable "context" {
  type = any

  description = "Context data"
}
