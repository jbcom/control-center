# Generate a random ID for the username suffix
resource "random_id" "hevo_readonly_user_suffix" {
  byte_length = 3
}

# Generate a secure random password for the Hevo read-only user
resource "random_password" "hevo_readonly_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+."
  min_lower        = 2
  min_upper        = 2
  min_numeric      = 2
  min_special      = 2
}

# Create AWS Secrets Manager secret for storing the password
resource "aws_secretsmanager_secret" "hevo_readonly_password" {
  name        = "/postgres/${var.cluster_name}/hevo/readonly/password"
  description = "Password for Hevo read-only PostgreSQL user"

  tags = var.tags
}

# Store the password in AWS Secrets Manager
resource "aws_secretsmanager_secret_version" "hevo_readonly_password" {
  secret_id     = aws_secretsmanager_secret.hevo_readonly_password.id
  secret_string = random_password.hevo_readonly_password.result
}

# Create a read-only user for Hevo data pipeline operations
resource "postgresql_role" "hevo_readonly_user" {
  provider = postgresql.postgres

  name     = "${var.username_prefix}${random_id.hevo_readonly_user_suffix.hex}"
  login    = true
  password = random_password.hevo_readonly_password.result
  roles    = var.roles
}

# Grant necessary privileges to the Hevo user for the database
resource "postgresql_grant" "hevo_database_connect" {
  provider    = postgresql.postgres
  database    = var.database_name
  role        = postgresql_role.hevo_readonly_user.name
  object_type = "database"
  privileges  = ["CONNECT"]
}

# Grant schema usage privileges
resource "postgresql_grant" "hevo_schema_usage" {
  provider    = postgresql.postgres
  database    = var.database_name
  role        = postgresql_role.hevo_readonly_user.name
  schema      = var.schema_name
  object_type = "schema"
  privileges  = ["USAGE"]
}

# Grant SELECT privileges on all tables in the schema
resource "postgresql_grant" "hevo_tables_select" {
  provider    = postgresql.postgres
  database    = var.database_name
  role        = postgresql_role.hevo_readonly_user.name
  schema      = var.schema_name
  object_type = "table"
  privileges  = ["SELECT"]
}

# Set default privileges for future tables
resource "postgresql_default_privileges" "hevo_future_tables_select" {
  provider    = postgresql.postgres
  database    = var.database_name
  role        = postgresql_role.hevo_readonly_user.name
  schema      = var.schema_name
  owner       = var.table_owner
  object_type = "table"
  privileges  = ["SELECT"]
}

# Grant rds_replication role for log-based incremental replication
resource "postgresql_grant_role" "hevo_replication_role" {
  provider   = postgresql.postgres
  role       = postgresql_role.hevo_readonly_user.name
  grant_role = "rds_replication"
}
