locals {
  vpc_id      = var.context.vpc_id
  subnet_ids  = var.context.elasticache_subnets
  kms_key_arn = var.kms_key_arn != "" ? var.kms_key_arn : var.context.kms_key_arn

  mq_admin_user_enabled = var.engine_type == "ActiveMQ"

  mq_admin_user_is_set = var.mq_admin_user != null && var.mq_admin_user != ""
  mq_admin_user        = local.mq_admin_user_is_set ? var.mq_admin_user : join("", random_string.mq_admin_user.*.result)

  mq_admin_password_is_set = var.mq_admin_password != null && var.mq_admin_password != ""
  mq_admin_password        = local.mq_admin_password_is_set ? var.mq_admin_password : join("", random_password.mq_admin_password.*.result)

  mq_application_user_is_set = var.mq_application_user != null && var.mq_application_user != ""
  mq_application_user        = local.mq_application_user_is_set ? var.mq_application_user : join("", random_string.mq_application_user.*.result)

  mq_application_password_is_set = var.mq_application_password != null && var.mq_application_password != ""
  mq_application_password        = local.mq_application_password_is_set ? var.mq_application_password : join("", random_password.mq_application_password.*.result)
  mq_logs                        = { logs = { "general_log_enabled" : var.general_log_enabled, "audit_log_enabled" : var.audit_log_enabled } }

  primary_ssl_endpoint = try(aws_mq_broker.default[0].instances[0].endpoints[0], "")

  mq_host          = trimprefix(local.primary_ssl_endpoint, "amqps://")
  mq_host_and_port = split(":", local.mq_host)
  mq_port          = element(local.mq_host_and_port, length(local.mq_host_and_port) - 1)
  mq_conn          = format("amqps://%s:%s@%s", local.mq_application_user, local.mq_application_password, local.mq_host)

  security_group_enabled = var.enabled && var.security_group_enabled

  tags = merge(var.context.tags, {
    Name = var.broker_name
  })
}