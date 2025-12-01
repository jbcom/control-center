variable "kms_key_arn" {
  type = string

  default = ""

  description = "KMS key ARN to grant access to"
}

variable "kms_key_arns" {
  type = list(string)

  default = []

  description = "KMS key ARNs to grant access to"
}

variable "operations" {
  type = list(string)

  default = ["Encrypt", "Decrypt"]

  description = "Operations to grant"
}

variable "grantee_principal" {
  type = string

  default = ""

  description = "Grantee principal"
}

variable "grantee_principals" {
  type = list(string)

  default = []

  description = "Grantee principals"
}