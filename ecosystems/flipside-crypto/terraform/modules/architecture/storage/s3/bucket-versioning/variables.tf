variable "bucket_name" {
  type = string

  description = "Bucket name"
}

variable "enabled" {
  type = bool

  default = true

  description = "Whether to enable versioning or not"
}
