variable "bucket_name" {
  type = string

  description = "Bucket name for the delivery stream"
}

variable "bucket_arn" {
  type = string

  description = "Bucket arn for the delivery stream"
}

variable "enabled" {
  type = bool

  default = true

  description = "Whether to enable the delivery stream or not"
}

variable "context" {
  type = any

  description = "Context data"
}