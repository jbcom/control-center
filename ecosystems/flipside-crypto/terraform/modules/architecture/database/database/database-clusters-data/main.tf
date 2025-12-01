module "cluster_label" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  name = var.rds_cluster_name

  environment = var.rds_cluster_environment

  tags = var.rds_cluster_tags

  label_order = ["name"]
}

data "aws_rds_cluster" "default" {
  cluster_identifier = var.rds_cluster_name
}

data "aws_db_instance" "default" {
  for_each = toset(data.aws_rds_cluster.default.cluster_members)

  db_instance_identifier = each.key
}

locals {
  rds_cluster_raw_data          = data.aws_rds_cluster.default
  rds_cluster_instance_raw_data = data.aws_db_instance.default

  dbi_resource_ids = distinct(flatten([
    for _, instance_data in local.rds_cluster_instance_raw_data : instance_data["resource_id"]
  ]))

  db_port = coalesce(one(distinct([
    for _, instance_data in local.rds_cluster_instance_raw_data : instance_data["db_instance_port"] if instance_data["db_instance_port"] > 0
  ])), 5432)

  rds_cluster_security_group_ids = distinct(flatten([
    for _, instance_data in local.rds_cluster_instance_raw_data : instance_data["vpc_security_groups"]
  ]))
}

data "aws_security_group" "default" {
  count = length(local.rds_cluster_security_group_ids)

  id = local.rds_cluster_security_group_ids[count.index]
}

locals {
  rds_cluster_security_group_data = data.aws_security_group.default

  rds_cluster_data = merge(module.cluster_label, {
    for k, v in module.cluster_label["tags"] : lower(k) => v
    }, {
    arn                     = local.rds_cluster_raw_data["arn"]
    cluster_identifier      = local.rds_cluster_raw_data["cluster_identifier"]
    cluster_resource_id     = local.rds_cluster_raw_data["cluster_resource_id"]
    cluster_security_groups = local.rds_cluster_security_group_ids
    database_name           = local.rds_cluster_raw_data["database_name"]
    dbi_resource_ids        = local.dbi_resource_ids
    endpoint                = local.rds_cluster_raw_data["endpoint"]
    master_host             = local.rds_cluster_raw_data["endpoint"]
    master_username         = local.rds_cluster_raw_data["master_username"]
    reader_endpoint         = local.rds_cluster_raw_data["reader_endpoint"]
    replicas_host           = ""
    security_group_arn      = try(local.rds_cluster_security_group_data.0.arn, "")
    security_group_id       = try(local.rds_cluster_security_group_data.0.id, "")
    security_group_name     = try(local.rds_cluster_security_group_data.0.name, "")
    db_name                 = local.rds_cluster_raw_data["database_name"]
    db_port                 = local.db_port
    publicly_accessible = anytrue([
      for _, instance_data in local.rds_cluster_instance_raw_data : instance_data["publicly_accessible"]
    ])
  })
}

resource "null_resource" "tagger" {
  count = var.tag_cluster ? 1 : 0

  triggers = {
    databases = jsonencode({
      for db_instance, db_params in local.rds_cluster_instance_raw_data : db_instance => db_params["db_instance_arn"]
    })

    tags = jsonencode(module.cluster_label.tags)
  }

  provisioner "local-exec" {
    command     = "${path.module}/bin/tagger.py"
    interpreter = ["python3.9"]
    environment = {
      AWS_REGION           = var.aws_region
      AWS_ASSUMED_ROLE_ARN = var.aws_assumed_role_arn
      DATABASES            = self.triggers.databases
      TAGS                 = self.triggers.tags
    }
  }
}
