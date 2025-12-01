variable "name" {
  type        = string
  description = "The name of the webhook"
}

variable "target_pipeline" {
  type        = string
  description = "The name of the pipeline"
}

variable "target_action" {
  type        = string
  description = "The name of the action in a pipeline you want to connect to the webhook. The action must be from the source (first) stage of the pipeline"
  default     = "Source"
}

variable "secret_token" {
  type        = string
  description = "The shared secret for the GitHub repository webhook"
  default     = ""
}

variable "repository" {
  type        = string
  description = "The repository of the webhook"
  default     = ""
}

variable "repositories" {
  type        = list(string)
  description = "List of repositories for the webhook"
  default     = []
}

locals {
  repositories = compact(concat([var.repository], var.repositories))
}

variable "events" {
  type        = list(string)
  description = "A list of events which should trigger the webhook"
  default     = ["push"]
}

variable "filter_json_path" {
  default     = "$.ref"
  type        = string
  description = "The JSON path to filter on."
}

variable "filter_match_equals" {
  default     = "refs/heads/{Branch}"
  type        = string
  description = "The value to match on (e.g. refs/heads/{Branch})."
}