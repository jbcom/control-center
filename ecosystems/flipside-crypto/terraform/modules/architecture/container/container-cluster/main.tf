locals {
  environment_name = var.context["environment"]
  account_data     = var.context["cluster_accounts_by_environment"][local.environment_name]
  tags             = var.context["tags"]
}

resource "aws_cloudwatch_log_group" "default" {
  name = "/ecs/cluster"

  retention_in_days = local.environment_name == "stg" ? 7 : 90

  tags = local.tags
}

resource "aws_ecs_cluster" "default" {
  name = var.context["id"]

  tags = local.tags

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.default.name
      }
    }
  }
}

locals {
  default_capacity_provider_strategy = {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

resource "aws_ecs_cluster_capacity_providers" "default" {
  cluster_name = aws_ecs_cluster.default.name

  capacity_providers = [
    "FARGATE",
    "FARGATE_SPOT",
  ]

  default_capacity_provider_strategy {
    base              = local.default_capacity_provider_strategy["base"]
    weight            = local.default_capacity_provider_strategy["weight"]
    capacity_provider = local.default_capacity_provider_strategy["capacity_provider"]
  }
}

#module "eks" {
#  for_each = {
#    for cluster_name, cluster_config in local.containers_config["clusters"] : cluster_name => cluster_config
#    if cluster_config["environment"] == local.environment_name
#  }
#
#  source  = "terraform-aws-modules/eks/aws"
#  version = "19.21"
#
#  cluster_name    = each.key
#  cluster_version = "1.28"
#
#  cluster_addons = {
#    coredns = {
#      most_recent       = true
#      resolve_conflicts = "OVERWRITE"
#    }
#    kube-proxy = {
#      most_recent       = true
#      resolve_conflicts = "OVERWRITE"
#    }
#    vpc-cni = {
#      most_recent       = true
#      resolve_conflicts = "OVERWRITE"
#    }
#  }
#
#  vpc_id     = local.vpc_id
#  subnet_ids = local.private_subnet_ids
#
#  eks_managed_node_groups = {
#    primary = {
#      instance_types = each.value["instance_types"]
#
#      min_size     = each.value["min_size"]
#      max_size     = each.value["max_size"]
#      desired_size = each.value["min_size"]
#    }
#  }
#
#  attach_cluster_encryption_policy = true
#}

locals {
  records_config = {
    cluster_name                       = aws_ecs_cluster.default.name
    cluster_arn                        = aws_ecs_cluster.default.arn
    cluster_id                         = aws_ecs_cluster.default.id
    cluster_log_group                  = aws_cloudwatch_log_group.default.name
    capacity_providers                 = aws_ecs_cluster_capacity_providers.default.capacity_providers
    default_capacity_provider_strategy = local.default_capacity_provider_strategy
  }
}

module "permanent_record" {
  source = "../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}