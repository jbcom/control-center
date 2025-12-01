locals {
  mongodb_atlas_config = var.context["mongodb_atlas"]

  mongodb_network_config = one([
    for region_config in var.context["mongodb_atlas"]["networks"]["regions"] : region_config if region_config["name"] == var.mongodb_aws_region
  ])

  enabled = local.mongodb_network_config["enabled"]

  mongodb_organization_config = local.mongodb_atlas_config["organization"]
  mongodb_organization_id     = local.mongodb_organization_config["id"]

  aws_region = lower(replace(var.mongodb_aws_region, "_", "-"))
}

resource "aws_vpc_ipam_pool_cidr_allocation" "default" {
  count = local.enabled ? 1 : 0

  ipam_pool_id = var.ipam_pool_id
  cidr         = var.cidr_block

  description = "${var.mongodb_aws_region} allocation"
}

moved {
  from = aws_vpc_ipam_pool_cidr_allocation.default
  to   = aws_vpc_ipam_pool_cidr_allocation.default[0]
}

resource "mongodbatlas_project" "default" {
  count = local.enabled ? 1 : 0

  name   = local.aws_region
  org_id = local.mongodb_organization_id
}

moved {
  from = mongodbatlas_project.default
  to   = mongodbatlas_project.default[0]
}

locals {
  project_id = join("", mongodbatlas_project.default.*.id)
}

resource "mongodbatlas_network_container" "default" {
  count = local.enabled ? 1 : 0

  project_id       = local.project_id
  atlas_cidr_block = var.cidr_block
  provider_name    = "AWS"
  region_name      = var.mongodb_aws_region
}

locals {
  container_id = join("", mongodbatlas_network_container.default.*.id)
}

resource "mongodbatlas_project_ip_access_list" "default" {
  for_each = local.enabled ? toset(local.allowed_cidr_blocks) : []

  project_id = local.project_id
  cidr_block = each.key
  comment    = "Managed by Terraform"
}

resource "mongodbatlas_custom_dns_configuration_cluster_aws" "default" {
  count = local.enabled ? 1 : 0

  project_id = local.project_id
  enabled    = length(local.mongodb_network_config["links"]) > 0
}

moved {
  from = mongodbatlas_custom_dns_configuration_cluster_aws.default
  to   = mongodbatlas_custom_dns_configuration_cluster_aws.default[0]
}

locals {
  records_config = merge(local.mongodb_network_config, {
    project_id          = local.project_id
    container_id        = local.container_id
    atlas_cidr_block    = join("", mongodbatlas_network_container.default.*.atlas_cidr_block)
    allowed_cidr_blocks = local.allowed_cidr_blocks
  })
}

module "permanent_record" {
  source = "../../utils/permanent-record"


  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}