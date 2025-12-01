variable "rds_databases" {
  description = "Map of database names and their RDS parameters"
  type = map(object({
    username              = string
    database_name         = optional(string)
    instance_type         = string
    instance_type_replica = string
    replica_count         = number
    publicly_accessible   = bool
    logical_replication   = bool
    engine_version        = optional(string)
    autoscaling           = optional(bool)
    environment_key       = optional(string)
  }))
}

variable "default_engine_version" {
  type = string

  default = "13.4"

  description = "Default engine version"
}

variable "primary_zone_id" {
  type = string

  default = ""

  description = "Primary zone ID to create an alias for"
}

variable "secondary_zone_ids" {
  type = list(string)

  default = []

  description = "Zone IDs to create aliases in"
}

variable "allowed_security_groups" {
  type = list(string)

  default = []

  description = "Allowed security groups"
}

variable "allowed_cidr_blocks" {
  type = list(string)

  default = []

  description = "Allowed CIDR blocks"
}

variable "kms_key_arn" {
  type = string

  default = ""

  description = "KMS key ARN"
}

variable "context" {
  type = any

  default = {}

  description = "Department and environment context"
}