locals {
  aws_region = var.context["mongodb_atlas"]["regions"][var.mongodb_aws_region]

  project_data = var.context["mongodb_atlas_project"]
  project_id   = local.project_data["project_id"]

  enabled = local.project_data["enabled"] && contains(var.config.networks, var.mongodb_aws_region)

  tags = var.context.tags
}

locals {
  cluster_name = coalesce(var.config.cluster_name, "${var.cluster_id}-${local.aws_region}")
}

resource "mongodbatlas_cluster" "default" {
  count = local.enabled && var.config.auto_scaling_compute_enabled ? 0 : 1

  project_id                                      = local.project_id
  provider_name                                   = var.config.cloud_provider
  provider_region_name                            = var.mongodb_aws_region
  name                                            = local.cluster_name
  provider_instance_size_name                     = var.config.instance_type
  mongo_db_major_version                          = var.config.mongodb_major_ver
  cluster_type                                    = var.config.cluster_type
  num_shards                                      = var.config.num_shards
  cloud_backup                                    = var.config.cloud_backup
  pit_enabled                                     = var.config.pit_enabled
  disk_size_gb                                    = var.config.disk_size_gb
  auto_scaling_disk_gb_enabled                    = var.config.auto_scaling_disk_gb_enabled
  provider_volume_type                            = var.config.volume_type
  provider_disk_iops                              = var.config.provider_disk_iops
  provider_auto_scaling_compute_min_instance_size = var.config.provider_auto_scaling_compute_min_instance_size
  provider_auto_scaling_compute_max_instance_size = var.config.provider_auto_scaling_compute_max_instance_size
  auto_scaling_compute_enabled                    = var.config.auto_scaling_compute_enabled
  auto_scaling_compute_scale_down_enabled         = var.config.auto_scaling_compute_scale_down_enabled
}

resource "mongodbatlas_cluster" "ignore_instance_size" {
  count = local.enabled && var.config.auto_scaling_compute_enabled ? 1 : 0

  project_id                                      = local.project_id
  provider_name                                   = var.config.cloud_provider
  provider_region_name                            = var.mongodb_aws_region
  name                                            = local.cluster_name
  provider_instance_size_name                     = var.config.instance_type
  mongo_db_major_version                          = var.config.mongodb_major_ver
  cluster_type                                    = var.config.cluster_type
  num_shards                                      = var.config.num_shards
  cloud_backup                                    = var.config.cloud_backup
  pit_enabled                                     = var.config.pit_enabled
  disk_size_gb                                    = var.config.disk_size_gb
  auto_scaling_disk_gb_enabled                    = var.config.auto_scaling_disk_gb_enabled
  provider_volume_type                            = var.config.volume_type
  provider_disk_iops                              = var.config.provider_disk_iops
  provider_auto_scaling_compute_min_instance_size = var.config.provider_auto_scaling_compute_min_instance_size
  provider_auto_scaling_compute_max_instance_size = var.config.provider_auto_scaling_compute_max_instance_size
  auto_scaling_compute_enabled                    = var.config.auto_scaling_compute_enabled
  auto_scaling_compute_scale_down_enabled         = var.config.auto_scaling_compute_scale_down_enabled


  lifecycle {
    ignore_changes = [
      provider_instance_size_name,
    ]
  }
}

moved {
  from = mongodbatlas_cluster.cluster
  to   = mongodbatlas_cluster.ignore_instance_size[0]
}

resource "random_password" "user_password" {
  count = local.enabled ? 1 : 0

  length  = 24
  special = false
}

moved {
  from = random_password.user_password
  to   = random_password.user_password[0]
}

resource "mongodbatlas_database_user" "default" {
  count = local.enabled ? 1 : 0

  username           = var.config.user_name
  password           = local.password
  project_id         = local.project_id
  auth_database_name = var.config.auth_database_name

  dynamic "roles" {
    for_each = local.databases

    content {
      role_name     = roles.value
      database_name = roles.key
    }
  }
}

moved {
  from = mongodbatlas_database_user.default
  to   = mongodbatlas_database_user.default[0]
}

locals {
  cluster_data_raw = {
    autoscaling = one(mongodbatlas_cluster.ignore_instance_size.*)
    fixed       = one(mongodbatlas_cluster.default.*)
  }

  cluster_data_key = var.config.auto_scaling_compute_enabled ? "autoscaling" : "fixed"
  cluster_data     = local.cluster_data_raw[local.cluster_data_key]
  raw_url_data     = one(local.cluster_data["connection_strings"])
  base_url_data = {
    privatelink = try(one(local.raw_url_data["private_endpoint"])["connection_string"], "")
    standard    = local.raw_url_data["standard"]
  }

  url_key = length(local.project_data["links"]) > 0 ? "privatelink" : "standard"
  url     = local.base_url_data[local.url_key]

  url_no_prefix        = trimprefix(local.url, "mongodb://")
  url_split_at_options = split("?", local.url_no_prefix)

  user_name = join("", mongodbatlas_database_user.default.*.username)
  password  = join("", random_password.user_password.*.result)

  databases = merge({
    (var.config.auth_database_name) = "dbAdminAnyDatabase"
  }, var.config.databases)

  connection_strings = {
    for database_name, _ in local.databases : database_name => format("mongodb://%s:%s@%s%s?%s", local.user_name, local.password, local.url_split_at_options[0], database_name, local.url_split_at_options[1])
  }
}

resource "aws_ssm_parameter" "password" {
  count = local.enabled ? 1 : 0

  provider = aws.root

  name  = "/root/databases/mongodb-atlas/${local.cluster_name}/password"
  type  = "SecureString"
  value = local.password

  overwrite = true

  tags = local.tags
}

moved {
  from = aws_ssm_parameter.password
  to   = aws_ssm_parameter.password[0]
}

resource "aws_ssm_parameter" "connection_string" {
  for_each = {
    for database_name, connection_string in local.connection_strings : database_name => connection_string if local.enabled
  }

  provider = aws.root

  name  = "/root/databases/mongodb-atlas/${local.cluster_name}/connection-strings/${each.key}"
  type  = "SecureString"
  value = each.value

  overwrite = true

  tags = local.tags
}

locals {
  records_config = {
    cluster_id = local.cluster_data["cluster_id"]
    user_name  = local.user_name
    password   = trimprefix(join("", aws_ssm_parameter.password.*.name), "/root")
    url        = local.url
    connection_strings = {
      for database_name, param_data in aws_ssm_parameter.connection_string : database_name => trimprefix(param_data["name"], "/root")
    }
  }
}

module "permanent_record" {
  source = "../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}
