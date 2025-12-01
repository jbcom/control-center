data "aws_caller_identity" "selected" {}

locals {
  account_id = data.aws_caller_identity.selected.account_id
}

data "aws_region" "selected" {}

locals {
  region = data.aws_region.selected.name
}

data "aws_efs_file_system" "compass" {
  for_each = toset(local.compass_environments)

  tags = {
    Name = "compass-us-east-1-compass-${each.key}-private"
  }
}

locals {
  efs_filesystem_ids = {
    for environment_name, efs_filesystem_data in data.aws_efs_file_system.compass : environment_name =>
    efs_filesystem_data.id
  }
}

locals {
  raw_compass_db_data = var.context["compass_databases"]
}

module "rds_cluster_writer_instance_data_query" {
  for_each          = local.raw_compass_db_data
  source            = "digitickets/cli/aws"
  version           = "7.0.0"
  role_session_name = format("GetRdsAccessFor%s", title(each.key))
  assume_role_arn   = local.compass_account["execution_role_arn"]
  aws_cli_commands = ["rds", "describe-db-clusters", "--db-cluster-identifier",
  "compass-us-east-1-compass-${each.key}-public"]
  aws_cli_query = "DBClusters[*].DBClusterMembers[?IsClusterWriter == `true`].DBInstanceIdentifier|[0]|[0]"
}

locals {
  compass_db_writer_instance_ids = {
    for environment_name, results in module.rds_cluster_writer_instance_data_query : environment_name => results.result
  }
}


data "aws_db_instance" "compass_db_instance" {
  for_each = local.compass_db_writer_instance_ids

  db_instance_identifier = each.value
}

locals {
  compass_db_data = {
    for environment_name, db_instance in local.compass_db_writer_instance_ids : environment_name =>
    merge(local.raw_compass_db_data[environment_name], data.aws_db_instance.compass_db_instance[environment_name])
  }
}

data "aws_ami" "latest_ubuntu_lts" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}
