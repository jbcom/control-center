variable "role_arn" {
  type = string

  description = "Role ARN"
}

variable "data" {
  type = any

  description = "S3 bucket data"
}

variable "config" {
  type = any

  description = "S3 bucket config"
}

variable "context" {
  type = any

  description = "Context data"
}