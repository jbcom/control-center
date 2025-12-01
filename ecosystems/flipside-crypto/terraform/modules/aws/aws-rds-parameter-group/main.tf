resource "random_pet" "group_name" {
  prefix    = var.prefix
  separator = "-"
}

locals {
  group_name = random_pet.group_name.id
}

resource "aws_db_parameter_group" "this" {
  name   = local.group_name
  family = var.engine_family
  tags   = local.tags

  dynamic "parameter" {
    for_each = var.group_parameters != {} ? var.group_parameters : local.default_parameters

    content {
      name         = parameter.key
      value        = parameter.value
      apply_method = "pending-reboot"
    }
  }
}

resource "aws_rds_cluster_parameter_group" "this" {
  count = var.enable_cluster_parameter_group ? 1 : 0

  name   = local.group_name
  family = var.engine_family
  tags   = local.tags

  dynamic "parameter" {
    for_each = var.cluster_parameters != {} ? var.cluster_parameters : (var.enable_replication ? merge({
      "rds.logical_replication" = 1
      wal_sender_timeout        = 0
    }, local.default_parameters) : local.default_parameters)

    content {
      name         = parameter.key
      value        = parameter.value
      apply_method = "pending-reboot"
    }
  }
}