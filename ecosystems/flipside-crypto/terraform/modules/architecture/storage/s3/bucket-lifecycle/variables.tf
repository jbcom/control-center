variable "bucket_name" {
  type = string

  description = "Bucket name for the delivery stream"
}

variable "config" {
  type = object({
    enabled                     = bool
    max_days                    = number
    max_noncurrent_days         = number
    max_noncurrent_versions     = number
    transition_to               = string
    transition_after            = number
    noncurrent_transition_to    = string
    noncurrent_transition_after = number
  })

  description = "When to transition for noncurrent"
}
