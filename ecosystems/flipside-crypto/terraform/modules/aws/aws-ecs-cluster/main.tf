locals {
  tags = var.context["tags"]

  networking_data    = var.context["cluster_networking"]
  vpc_id             = local.networking_data["vpc_id"]
  private_subnet_ids = local.networking_data["private_subnet_ids"]

  allowed_cidr_blocks = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
  ]
}

resource "aws_cloudwatch_log_group" "default" {
  name = "/indexers/clusters/${var.cluster_name}"

  retention_in_days = 90

  tags = local.tags
}

resource "aws_ecs_cluster" "default" {
  name = var.cluster_name

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

module "cluster_instance_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.22.0"

  name = var.cluster_config.name

  enabled = var.cluster_config.launch_type == "EC2"

  attributes = ["cluster", "instance"]

  instance_profile_enabled = true

  policy_description = "Managed by Terraform"
  role_description   = "Managed by Terraform"

  principals = {
    Service = ["ec2.amazonaws.com"]
  }

  policy_documents = [
    file("${path.module}/policies/cluster-instance-policy.json"),
  ]

  managed_policy_arns = concat([
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonEC2RoleforSSM",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/CloudWatchLogsFullAccess",
    ], length(module.cluster_secrets.policy_documents) > 0 ? [
    module.cluster_secrets_policy.policy_arn,
  ] : [])

  context = var.context
}

module "cluster_security_group" {
  source  = "cloudposse/security-group/aws"
  version = "2.2.0"

  name = var.cluster_config.name

  enabled = var.cluster_config.launch_type == "EC2"

  attributes = ["cluster"]

  allow_all_egress = true

  rules = [
    for cidr_block in local.allowed_cidr_blocks : {
      key         = cidr_block
      type        = "ingress"
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = [cidr_block]
      self        = null
      description = "Allow all traffic from ${cidr_block}"
    }
  ]

  vpc_id = local.vpc_id

  target_security_group_id = var.cluster_config.launch_type == "EC2" ? [] : [
    local.networking_data["vpc_default_security_group_id"],
  ]

  context = var.context
}

locals {
  cluster_security_group_id = module.cluster_security_group["id"]
}

module "autoscaling_group" {
  source  = "cloudposse/ec2-autoscale-group/aws"
  version = "0.43.0"

  name = var.cluster_config.name

  enabled = var.cluster_config.launch_type == "EC2"

  attributes = ["cluster", "instance"]

  image_id                                = data.aws_ami.amazon_linux_2.image_id
  instance_type                           = var.cluster_config.instance_type
  security_group_ids                      = [local.cluster_security_group_id]
  subnet_ids                              = local.private_subnet_ids
  health_check_type                       = "EC2"
  min_size                                = var.cluster_config.min_size
  max_size                                = var.cluster_config.max_size
  associate_public_ip_address             = false
  key_name                                = var.cluster_config.key_pair_name
  metadata_http_tokens_required           = false
  metadata_instance_metadata_tags_enabled = true
  iam_instance_profile_name               = module.cluster_instance_role.instance_profile
  autoscaling_policies_enabled            = false
  protect_from_scale_in                   = true

  user_data_base64 = base64encode(templatefile("${path.module}/templates/user_data.tpl", {
    cluster_name = var.cluster_name
  }))

  target_group_arns = concat([
    var.cluster_config.default_target_group_arn,
    ], [
    for _, target_group_data in var.cluster_config.target_groups : target_group_data["arn"]
  ])

  enable_monitoring = true

  tags = {
    AmazonECSManaged = true
  }

  context = var.context
}

resource "aws_ecs_capacity_provider" "default" {
  count = var.cluster_config.launch_type == "EC2" ? 1 : 0

  name = var.cluster_name

  auto_scaling_group_provider {
    auto_scaling_group_arn         = module.autoscaling_group["autoscaling_group_arn"]
    managed_termination_protection = "ENABLED"

    managed_scaling {
      status = "ENABLED"
    }
  }
}

resource "aws_ecs_cluster_capacity_providers" "default" {
  cluster_name = aws_ecs_cluster.default.name

  capacity_providers = concat([
    "FARGATE",
    "FARGATE_SPOT",
    ], var.cluster_config.launch_type == "EC2" ? [
    aws_ecs_capacity_provider.default.0.name,
  ] : [])

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = var.cluster_config.launch_type == "EC2" ? aws_ecs_capacity_provider.default.0.name : "FARGATE"
  }
}

module "cluster_secrets" {
  source = "../read-and-store-secrets"

  secret_files               = var.cluster_config.secrets
  secret_manager_name_prefix = "/indexers/${var.cluster_name}"
  secrets_dir                = var.secrets_dir

  context = var.context
}

locals {
  datadog_data = var.context["indexers"]["datadog"]
}

module "cluster_secrets_policy" {
  source  = "cloudposse/iam-policy/aws"
  version = "2.0.2"

  name = var.cluster_config.name

  enabled = length(module.cluster_secrets.policy_documents) > 0

  attributes = ["cluster", "secrets"]

  iam_policy_enabled = true

  iam_source_policy_documents = concat(local.datadog_data["policy_documents"], module.cluster_secrets.policy_documents)

  context = var.context
}

module "efs" {
  for_each = toset(var.cluster_config.volumes)

  source  = "cloudposse/efs/aws"
  version = "1.4.0"

  name = var.cluster_name

  region = data.aws_region.current.name

  attributes = split("/", each.key)

  vpc_id  = local.vpc_id
  subnets = local.private_subnet_ids

  allowed_cidr_blocks = local.allowed_cidr_blocks

  efs_backup_policy_enabled = true

  kms_key_id = var.context["kms"]["indexers-architecture"]["kms_key_arn"]

  context = var.context
}