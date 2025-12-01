resource "aws_db_parameter_group" "db_instance_prod" {
  description = "DB instance parameter group"
  family      = "aurora-postgresql14"
  name        = "compass-us-east-1-compass-prod-public-20230221220447335100000006"

  parameter {
    apply_method = "immediate"
    name         = "log_min_duration_statement"
    value        = "4000"
  }

  parameter {
    apply_method = "immediate"
    name         = "idle_in_transaction_session_timeout"
    value        = "600"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "pg_stat_statements.max"
    value        = "10000"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "pg_stat_statements.track"
    value        = "ALL"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "track_activity_query_size"
    value        = "4096"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "track_io_timing"
    value        = "1"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "shared_preload_libraries"
    value        = "pg_cron,pg_stat_statements,pglogical"
  }

  tags = merge(local.tags, {
    Name       = "compass-us-east-1-compass-prod-public-20230221220447335100000006"
    Attributes = "public"
  })
}

resource "aws_db_parameter_group" "db_instance_stg" {
  description = "DB instance parameter group"
  family      = "aurora-postgresql14"
  name        = "compass-us-east-1-compass-stg-public-20230221220447314700000003"

  parameter {
    apply_method = "immediate"
    name         = "log_min_duration_statement"
    value        = "4000"
  }

  parameter {
    apply_method = "immediate"
    name         = "idle_in_transaction_session_timeout"
    value        = "600"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "pg_stat_statements.max"
    value        = "10000"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "pg_stat_statements.track"
    value        = "ALL"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "track_activity_query_size"
    value        = "4096"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "track_io_timing"
    value        = "1"
  }

  parameter {
    apply_method = "pending-reboot"
    name         = "shared_preload_libraries"
    value        = "pg_cron,pg_stat_statements,pglogical"
  }

  tags = merge(local.tags, {
    Name       = "compass-us-east-1-compass-stg-public-20230221220447314700000003"
    Attributes = "public"
  })
}
