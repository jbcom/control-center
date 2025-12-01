locals {
  environment_name = var.context["environment"]
}

resource "random_password" "datadog_db_user_password" {
  length  = 24
  special = true
}

locals {
  datadog_db_user_password = random_password.datadog_db_user_password.result
}

resource "aws_ssm_parameter" "datadog_db_user_password" {
  name  = "/compass/${local.environment_name}/datadog/database/monitoring/user/password"
  type  = "SecureString"
  value = local.datadog_db_user_password

  tags = var.context["copilot_environment_tags"][local.environment_name]
}

# Create the datadog role
resource "postgresql_role" "datadog_role" {
  name     = "datadog"
  login    = true
  password = local.datadog_db_user_password
  roles    = ["pg_monitor"]
}

# Create the datadog schema
resource "postgresql_schema" "datadog_schema" {
  name  = "datadog"
  owner = postgresql_role.datadog_role.name
}

# Grant USAGE on schemas and assign monitoring privileges
resource "postgresql_grant" "datadog_schema_usage" {
  database    = var.database_name
  role        = postgresql_role.datadog_role.name
  schema      = "datadog"
  object_type = "schema"
  privileges  = ["USAGE", "CREATE"]
}

resource "postgresql_grant" "public_schema_usage" {
  database    = var.database_name
  role        = postgresql_role.datadog_role.name
  schema      = "public"
  object_type = "schema"
  privileges  = ["USAGE"]
}

# Create the pg_stat_statements extension
resource "postgresql_extension" "pg_stat_statements" {
  name     = "pg_stat_statements"
  database = var.database_name
  schema   = "public"
}

# Create the explain_statement function
resource "postgresql_function" "datadog_explain_statement" {
  name             = "explain_statement"
  schema           = "datadog"
  database         = var.database_name
  returns          = "SETOF json"
  language         = "plpgsql"
  security_definer = true
  body             = <<-EOF
    DECLARE
      curs REFCURSOR;
      plan JSON;
    BEGIN
      OPEN curs FOR EXECUTE pg_catalog.concat('EXPLAIN (FORMAT JSON) ', l_query);
      FETCH curs INTO plan;
      CLOSE curs;
      RETURN QUERY SELECT plan;
    END;
  EOF

  arg {
    name = "l_query"
    type = "text"
    mode = "IN"
  }

  arg {
    name = "explain"
    type = "json"
    mode = "OUT"
  }
}
