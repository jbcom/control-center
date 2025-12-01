variable "key_pair_name" {
  type = string

  description = "Key pair name"
}

variable "key_pair_path" {
  type = string

  default = null

  description = "Key pair path"
}

locals {
  key_pair_path = var.key_pair_path != null ? var.key_pair_path : "${path.root}/keys"
}

variable "write_key_pair_to_file" {
  type = bool

  default = false

  description = "Write the SSH key to a file"
}

variable "write_key_pair_to_github" {
  type = bool

  default = false

  description = "Write the SSH key to Github Actions"
}

variable "write_key_pair_to_aws" {
  type = bool

  default = true

  description = "Whether to write the keypair to AWS"
}

variable "save_secrets_to_aws" {
  type = bool

  default = false

  description = "Whether to save secrets to AWS Secrets Manager"
}

variable "secrets_manager_prefix" {
  type = string

  default = "/key-pairs"

  description = "Secrets Manager prefix"
}

variable "kms_key_arn" {
  type = string

  default = null

  description = "KMS key ARN for encryption"
}

variable "tags" {
  type = map(string)

  default = {}

  description = "Tags"
}