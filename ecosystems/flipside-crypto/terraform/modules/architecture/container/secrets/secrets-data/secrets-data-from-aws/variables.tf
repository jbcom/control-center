variable "secrets" {
  type = map(object({
    id   = string
    type = optional(string, "")
    path = optional(string, "")
  }))

  description = "Secrets to read from AWS by their output key and secret ID"
}
