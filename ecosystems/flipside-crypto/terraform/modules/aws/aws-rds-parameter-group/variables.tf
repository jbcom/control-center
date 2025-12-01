variable "prefix" {
  type = string

  description = "Prefix for all resource names"
}

variable "engine_family" {
  type = string

  default = "aurora-postgresql13"

  description = "Default engine family for the database parameter group"
}

variable "group_parameters" {
  type = map(string)

  default = {}

  description = <<EOT
If specified override generation of the group parameters with this map.
If set the value of shared_preload_libraries is ignored.
EOT
}

variable "cluster_parameters" {
  type = map(string)

  default = {}

  description = <<EOT
If specified override generation of the cluster parameters with this map.
If set the value of shared_preload_libraries is ignored.
EOT
}

variable "shared_preload_libraries" {
  type = list(string)

  default = [
    "pg_stat_statements",
    "pglogical",
  ]

  description = "Shared preload libraries"
}

variable "tags" {
  type = map(string)

  default = {}

  description = "Resource tags"
}

variable "enable_replication" {
  type = bool

  default = true

  description = "Whether to enable replication parameters"
}

variable "enable_cluster_parameter_group" {
  type = bool

  default = true

  description = "Whether to enable an additional cluster parameter group for RDS Aurora"
}