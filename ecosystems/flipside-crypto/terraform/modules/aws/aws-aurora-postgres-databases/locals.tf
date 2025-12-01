locals {
  kms_key_arn = var.kms_key_arn != "" ? var.kms_key_arn : try(var.context.kms_key_arn, null)

  rds_databases = {
    for name, params in var.rds_databases : name => defaults(params, {
      database_name   = name
      autoscaling     = params.replica_count > 0
      environment_key = format("%s_DATABASE", upper(name))
      engine_version  = var.default_engine_version
    })
  }

  rds_environment = [
    for name, params in module.rds : {
      format("%s_URL", local.rds_config[name].environment_key) = format("postgres://%s:%s@%s:%s/%s", params.cluster_master_username, params.cluster_master_password, aws_route53_record.rds[0].fqdn, params.cluster_port, params.cluster_database_name)
      format("%s_DSN", local.rds_config[name].environment_key) = format("user=%s password=%s host=%s port=%s database=%s", params.cluster_master_username, params.cluster_master_password, aws_route53_record.rds[0].fqdn, params.cluster_port, params.cluster_database_name)
    }
  ]

  environment_overrides = merge(local.rds_environment...)
}
