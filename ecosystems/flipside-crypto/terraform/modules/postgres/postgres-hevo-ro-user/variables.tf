variable "cluster_name" {
  description = "The name of the PostgreSQL cluster (e.g., 'product-eng-velocity-mark-2')"
  type        = string
}

variable "database_name" {
  description = "The name of the database to grant access to"
  type        = string
}

variable "schema_name" {
  description = "The name of the schema to grant access to"
  type        = string
  default     = "public"
}

variable "username_prefix" {
  description = "The prefix for the username (e.g., 'prod_platform_api_db_')"
  type        = string
}


variable "table_owner" {
  description = "The name of the database user who owns the tables (required for default privileges)"
  type        = string
}

variable "roles" {
  description = "Postgres roles"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}
