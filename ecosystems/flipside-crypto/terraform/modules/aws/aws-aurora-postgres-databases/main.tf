module "rds" {
  for_each = local.rds_databases

  source = "../aws-aurora-database-cluster"

  name           = each.key
  engine         = "aurora-postgresql"
  engine_version = each.value.engine_version
  instance_class = each.value.autoscaling ? each.value.instance_type_replica : each.value.instance_type
  instances = each.value.autoscaling ? {
    primary = {
      instance_class = each.value.instance_type
    }
    secondary = {}
    } : {
    primary = {}
  }

  kms_key_id        = local.kms_key_arn
  storage_encrypted = true

  performance_insights_enabled          = true
  performance_insights_kms_key_id       = var.context.kms_key_arn
  performance_insights_retention_period = var.context.environment != "prod" ? 7 : 731

  autoscaling_enabled      = each.value.autoscaling
  autoscaling_min_capacity = 1
  autoscaling_max_capacity = each.value.replica_count

  monitoring_interval           = 60
  iam_role_name                 = format("%s-%s-rds-monitoring", each.value.database_name, var.context.environment)
  iam_role_use_name_prefix      = true
  iam_role_description          = format("%s RDS enhanced monitoring IAM role", each.key)
  iam_role_path                 = "/autoscaling/"
  iam_role_max_session_duration = 7200

  iam_database_authentication_enabled = true

  subnets = each.value.publicly_accessible ? var.context.public_subnets : var.context.database_subnets
  vpc_id  = var.context.vpc_id

  allowed_security_groups = var.allowed_security_groups

  allowed_cidr_blocks = each.value.publicly_accessible ? ["0.0.0.0/0"] : var.allowed_cidr_blocks

  apply_immediately   = true
  skip_final_snapshot = false

  create_cluster         = true
  create_monitoring_role = true
  create_security_group  = true

  master_username        = each.value.username
  database_name          = each.value.database_name
  create_random_password = true
  random_password_length = 24

  db_subnet_group_name            = each.value.publicly_accessible ? each.key : var.context.database_subnet_group_name
  create_db_subnet_group          = each.value.publicly_accessible
  db_parameter_group_name         = each.value.logical_replication ? aws_db_parameter_group.pgsql-replication.id : aws_db_parameter_group.pgsql.id
  db_cluster_parameter_group_name = each.value.logical_replication ? aws_rds_cluster_parameter_group.pgsql-replication.id : aws_rds_cluster_parameter_group.pgsql.id

  enabled_cloudwatch_logs_exports = ["postgresql"]

  publicly_accessible = each.value.publicly_accessible
}
