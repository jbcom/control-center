variable "environment" {
  type = string

  default = null

  description = "Environment name"
}

variable "kms_key_arn" {
  type = string

  description = "KMS key ARN"
}

variable "secrets_kms_key_arn" {
  type = string

  default = null

  description = "Secrets KMS key ARN"
}

variable "kms_key_id" {
  type = string

  description = "KMS key ID"
}

variable "account" {
  type = object({
    json_key           = string
    domain             = string
    subdomain          = string
    execution_role_arn = optional(string)
  })

  description = "Account data"
}

variable "allowed_cidr_blocks" {
  type = object({
    public  = list(string)
    private = list(string)
  })

  default = {
    public = ["0.0.0.0/0"]
    private = [
      "10.0.0.0/8",
      "172.16.0.0/12",
      "192.168.0.0/16",
    ]
  }

  description = "Allowed CIDR blocks"
}

variable "networking" {
  type = object({
    vpc_id             = string
    vpc_cidr_block     = string
    public_subnet_ids  = list(string)
    private_subnet_ids = list(string)
  })

  description = "Networking data"
}

variable "infrastructure" {
  type = any

  description = "Infrastructure data"
}

variable "secret_policy" {
  type = string

  default = null

  description = "Secret policy to use instead of generating one"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "save_permanent_record" {
  type = bool

  default = true

  description = "Whether to save a permanent record"
}

variable "records_dir" {
  type = string

  description = "Records file directory"
}

variable "records_file_name" {
  type = string

  description = "Records file name"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
