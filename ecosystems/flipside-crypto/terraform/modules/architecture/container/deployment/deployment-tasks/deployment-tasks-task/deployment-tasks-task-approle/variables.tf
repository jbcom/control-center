variable "config" {
  type = object({
    enabled       = bool
    role_id_key   = string
    secret_id_key = string
  })

  description = "Approle configuration"
}