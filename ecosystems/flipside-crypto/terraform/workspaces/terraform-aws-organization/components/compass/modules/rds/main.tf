locals {
  tags = {
    Name      = "${var.name}-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}

# VPC
data "aws_vpc" "vpc" {
  tags = {
    Name = var.vpc_name
  }
}

# Subnets
data "aws_subnets" "all_ids" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.vpc.id]
  }
}

data "aws_subnet" "all" {
  for_each = toset(data.aws_subnets.all_ids.ids)
  id       = each.value
}

################################################################################
# RDS Aurora Module
################################################################################

module "aurora" {
  source = "terraform-aws-modules/rds-aurora/aws"

  name           = "${var.name}-${var.env}"
  engine         = "aurora-postgresql"
  engine_version = "14.5"
  instances = {
    1 = {
      instance_class      = var.instance_class
      publicly_accessible = true
    }
  }

  vpc_id                 = data.aws_vpc.vpc.id
  db_subnet_group_name   = var.public_db_subnet_group_name
  create_db_subnet_group = false
  create_security_group  = true

  allowed_cidr_blocks = concat(["0.0.0.0/0"], tolist([for s in data.aws_subnet.all : s.cidr_block]))

  iam_database_authentication_enabled = true
  master_password                     = random_password.master.result
  create_random_password              = false

  apply_immediately   = true
  skip_final_snapshot = true

  create_db_cluster_parameter_group      = true
  db_cluster_parameter_group_name        = "${var.name}-${var.env}"
  db_cluster_parameter_group_family      = "aurora-postgresql14"
  db_cluster_parameter_group_description = "${var.name}-${var.env} cluster parameter group"
  db_cluster_parameter_group_parameters = [
    {
      name         = "log_min_duration_statement"
      value        = 4000
      apply_method = "immediate"
      }, {
      name         = "rds.force_ssl"
      value        = 1
      apply_method = "immediate"
    }
  ]

  create_db_parameter_group      = true
  db_parameter_group_name        = "${var.name}-${var.env}"
  db_parameter_group_family      = "aurora-postgresql14"
  db_parameter_group_description = "${var.name}-${var.env} DB parameter group"
  db_parameter_group_parameters = [
    {
      name         = "log_min_duration_statement"
      value        = 4000
      apply_method = "immediate"
    }
  ]

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name        = "${var.name}-${var.env}"
    Environment = var.env
    Terraform   = "true"
  }
}

################################################################################
# Supporting Resources
################################################################################

resource "random_password" "master" {
  length  = 20
  special = false
}

resource "aws_ssm_parameter" "password" {
  name        = "/${var.name}/${var.env}/db/password/main"
  description = "RDS Password Main"
  type        = "SecureString"
  value       = random_password.master.result

  tags = local.tags
}

resource "aws_ssm_parameter" "user" {
  name        = "/${var.name}/${var.env}/db/user/main"
  description = "RDS User Main"
  type        = "SecureString"
  value       = module.aurora.cluster_master_username

  tags = local.tags
}

resource "aws_ssm_parameter" "host" {
  name        = "/${var.name}/${var.env}/db/host/write"
  description = "RDS Write Host"
  type        = "SecureString"
  value       = module.aurora.cluster_endpoint

  tags = local.tags
}

resource "aws_ssm_parameter" "port" {
  name        = "/${var.name}/${var.env}/db/port"
  description = "RDS Port"
  type        = "SecureString"
  value       = module.aurora.cluster_port

  tags = local.tags
}

resource "aws_ssm_parameter" "db_write_url" {
  name        = "/${var.name}/${var.env}/db/url/write"
  description = "RDS Write Url"
  type        = "SecureString"
  value       = "postgresql://${module.aurora.cluster_master_username}:${random_password.master.result}@${module.aurora.cluster_endpoint}:${module.aurora.cluster_port}"

  tags = local.tags
}


resource "aws_ssm_parameter" "app_db_write_url" {
  name        = "/${var.name}/${var.env}/app_db/url/write"
  description = "RDS Write Url"
  type        = "SecureString"
  value       = "postgresql://${module.aurora.cluster_master_username}:${random_password.master.result}@${module.aurora.cluster_endpoint}:${module.aurora.cluster_port}/postgres"

  tags = local.tags
}