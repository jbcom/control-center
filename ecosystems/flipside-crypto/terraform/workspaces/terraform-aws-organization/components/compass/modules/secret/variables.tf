variable "name" {
  type = string

  description = "Name for the SecretsManager secret"
}

variable "enabled" {
  type = bool

  default = true

  description = "Whether the secret is enabled or not"
}

variable "secret" {
  type = string

  sensitive = true

  description = "Secret"
}

variable "policy" {
  type = string

  default = null

  description = "Secret policy to apply to the secret"
}

variable "kms_key_arn" {
  type = string

  default = null

  description = "KMS key ARN"
}

variable "tags" {
  type = map(string)

  default = {}

  description = "Tags"
}