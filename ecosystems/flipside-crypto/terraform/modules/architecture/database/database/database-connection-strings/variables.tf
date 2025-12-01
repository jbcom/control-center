variable "config" {
  type = object({
    master_username = string
    endpoint        = string
    db_port         = optional(number, 5432)
    database_name   = string
    schema          = optional(string, "public")
    password        = string
  })

  sensitive = true

  description = "Database data"
}

variable "secret_suffix" {
  type = string

  description = "Suffix for both SecretsManager secrets"
}

variable "secret_policy" {
  type = string

  default = null

  description = "Secret policy to apply to the secrets"
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