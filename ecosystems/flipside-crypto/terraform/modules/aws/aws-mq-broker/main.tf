resource "random_string" "mq_admin_user" {
  count   = var.enabled && local.mq_admin_user_enabled && !local.mq_admin_user_is_set ? 1 : 0
  length  = 8
  special = false
  number  = false
}

resource "random_password" "mq_admin_password" {
  count   = var.enabled && local.mq_admin_user_enabled && !local.mq_admin_password_is_set ? 1 : 0
  length  = 16
  special = false
}

resource "random_string" "mq_application_user" {
  count   = var.enabled && !local.mq_application_user_is_set ? 1 : 0
  length  = 8
  special = false
  number  = false
}

resource "random_password" "mq_application_password" {
  count   = var.enabled && !local.mq_application_password_is_set ? 1 : 0
  length  = 16
  special = false
}

resource "aws_mq_broker" "default" {
  count                      = var.enabled && var.auto_minor_version_upgrade ? 1 : 0
  broker_name                = var.broker_name
  deployment_mode            = var.deployment_mode
  engine_type                = var.engine_type
  engine_version             = var.engine_version
  host_instance_type         = var.host_instance_type
  auto_minor_version_upgrade = var.auto_minor_version_upgrade
  apply_immediately          = var.apply_immediately
  publicly_accessible        = var.publicly_accessible
  subnet_ids                 = local.subnet_ids
  tags                       = local.tags

  security_groups = [module.security_group.id]

  dynamic "encryption_options" {
    for_each = var.encryption_enabled ? ["true"] : []
    content {
      kms_key_id        = local.kms_key_arn
      use_aws_owned_key = false
    }
  }

  # NOTE: Omit logs block if both general and audit logs disabled:
  # https://github.com/hashicorp/terraform-provider-aws/issues/18067
  dynamic "logs" {
    for_each = {
      for logs, type in local.mq_logs : logs => type
      if type.general_log_enabled || type.audit_log_enabled
    }
    content {
      general = logs.value["general_log_enabled"]
      audit   = logs.value["audit_log_enabled"]
    }
  }

  maintenance_window_start_time {
    day_of_week = var.maintenance_day_of_week
    time_of_day = var.maintenance_time_of_day
    time_zone   = var.maintenance_time_zone
  }

  dynamic "user" {
    for_each = local.mq_admin_user_enabled ? ["true"] : []
    content {
      username       = local.mq_admin_user
      password       = local.mq_admin_password
      groups         = ["admin"]
      console_access = true
    }
  }

  user {
    username = local.mq_application_user
    password = local.mq_application_password
  }

  lifecycle {
    ignore_changes = [
      engine_version,
    ]
  }
}

resource "aws_mq_broker" "default-no-auto-upgrade" {
  count                      = var.enabled && !var.auto_minor_version_upgrade ? 1 : 0
  broker_name                = var.broker_name
  deployment_mode            = var.deployment_mode
  engine_type                = var.engine_type
  engine_version             = var.engine_version
  host_instance_type         = var.host_instance_type
  auto_minor_version_upgrade = var.auto_minor_version_upgrade
  apply_immediately          = var.apply_immediately
  publicly_accessible        = var.publicly_accessible
  subnet_ids                 = local.subnet_ids
  tags                       = local.tags

  security_groups = [module.security_group.id]

  dynamic "encryption_options" {
    for_each = var.encryption_enabled ? ["true"] : []
    content {
      kms_key_id        = local.kms_key_arn
      use_aws_owned_key = false
    }
  }

  # NOTE: Omit logs block if both general and audit logs disabled:
  # https://github.com/hashicorp/terraform-provider-aws/issues/18067
  dynamic "logs" {
    for_each = {
      for logs, type in local.mq_logs : logs => type
      if type.general_log_enabled || type.audit_log_enabled
    }
    content {
      general = logs.value["general_log_enabled"]
      audit   = logs.value["audit_log_enabled"]
    }
  }

  maintenance_window_start_time {
    day_of_week = var.maintenance_day_of_week
    time_of_day = var.maintenance_time_of_day
    time_zone   = var.maintenance_time_zone
  }

  dynamic "user" {
    for_each = local.mq_admin_user_enabled ? ["true"] : []
    content {
      username       = local.mq_admin_user
      password       = local.mq_admin_password
      groups         = ["admin"]
      console_access = true
    }
  }

  user {
    username = local.mq_application_user
    password = local.mq_application_password
  }
}