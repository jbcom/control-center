locals {
  performance_insights_retention_period = var.performance_insights_retention_period != null ? var.performance_insights_retention_period : (var.context.environment != "prod" ? 7 : 731)
  iam_role_name                         = var.iam_role_name != null ? var.iam_role_name : "${var.database_name}-${var.context.environment}-rds-monitoring"

  vpc_id                 = var.vpc_id != "" ? var.vpc_id : var.context.vpc_id
  db_subnet_group_name   = var.db_subnet_group_name != "" ? var.db_subnet_group_name : (var.publicly_accessible ? each.key : var.context.database_subnet_group_name)
  create_db_subnet_group = var.db_subnet_group_name != lookup(var.context, "database_subnet_group_name", "") ? var.create_db_subnet_group : false
  subnets                = length(var.subnets) > 0 ? var.subnets : (var.publicly_accessible ? var.context.public_subnets : var.context.database_subnets)

  allowed_cidr_blocks = var.publicly_accessible ? ["0.0.0.0/0"] : var.allowed_cidr_blocks

  kms_key_id                      = var.kms_key_id != null ? var.kms_key_id : var.context.kms_key_id
  performance_insights_kms_key_id = var.performance_insights_kms_key_id != null ? var.performance_insights_kms_key_id : local.kms_key_id

  primary_zone_id = var.primary_zone_id != "" ? var.primary_zone_id : var.context.zone_id
  zone_ids        = compact(flatten(concat([local.primary_zone_id], var.secondary_zone_ids)))

  tags = merge(var.context.tags, var.tags, {
    Name     = var.database_name
    Database = var.database_name
    Username = var.master_username
  })
}