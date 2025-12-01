locals {
  project_data     = var.context["mongodb_atlas_projects"][var.mongodb_aws_region]
  project_id       = local.project_data["project_id"]
  atlas_cidr_block = local.project_data["atlas_cidr_block"]
  network_links    = local.project_data["links"]

  enabled = local.project_data["enabled"] && contains(local.network_links, var.json_key)

  resource_id = "mongodb-atlas-endpoint-${var.mongodb_aws_region}-${local.private_link_id}"
  tags = merge(var.context["tags"], {
    Name = local.resource_id
  })
}

resource "mongodbatlas_privatelink_endpoint" "endpoint" {
  count = local.enabled ? 1 : 0

  project_id    = local.project_id
  provider_name = "AWS"
  region        = local.region
}

moved {
  from = mongodbatlas_privatelink_endpoint.endpoint
  to   = mongodbatlas_privatelink_endpoint.endpoint[0]
}

locals {
  private_link_id       = join("", mongodbatlas_privatelink_endpoint.endpoint.*.private_link_id)
  endpoint_service_name = join("", mongodbatlas_privatelink_endpoint.endpoint.*.endpoint_service_name)
}

resource "aws_security_group" "endpoint" {
  count = local.enabled ? 1 : 0

  name        = "mongodb-atlas-endpoint-${var.mongodb_aws_region}-${local.private_link_id}"
  description = "VPC endpoint security group for ${local.endpoint_service_name}"
  vpc_id      = local.vpc_id

  tags = local.tags
}

moved {
  from = aws_security_group.endpoint
  to   = aws_security_group.endpoint[0]
}

locals {
  security_group_id = join("", aws_security_group.endpoint.*.id)
}

resource "aws_security_group_rule" "ingress" {
  count = local.enabled ? 1 : 0

  type = "ingress"

  security_group_id = local.security_group_id

  protocol  = "-1"
  from_port = 0
  to_port   = 0

  cidr_blocks = local.project_data["allowed_cidr_blocks"]
}

moved {
  from = aws_security_group_rule.ingress
  to   = aws_security_group_rule.ingress[0]
}

resource "aws_vpc_endpoint" "service" {
  count = local.enabled ? 1 : 0

  vpc_id            = local.vpc_id
  service_name      = local.endpoint_service_name
  vpc_endpoint_type = "Interface"
  subnet_ids        = local.network_data["private_subnet_ids"]
  security_group_ids = [
    local.security_group_id,
  ]
}

moved {
  from = aws_vpc_endpoint.service
  to   = aws_vpc_endpoint.service[0]
}

locals {
  vpc_endpoint_id = join("", aws_vpc_endpoint.service.*.id)
}

resource "mongodbatlas_privatelink_endpoint_service" "service" {
  count = local.enabled ? 1 : 0

  project_id          = local.project_id
  private_link_id     = local.private_link_id
  endpoint_service_id = local.vpc_endpoint_id
  provider_name       = "AWS"
}

moved {
  from = mongodbatlas_privatelink_endpoint_service.service
  to   = mongodbatlas_privatelink_endpoint_service.service[0]
}

locals {
  records_config = {
    mongodb_atlas_private_endpoints = {
      privatelink_endpoint         = one(mongodbatlas_privatelink_endpoint.endpoint.*)
      privatelink_endpoint_service = one(mongodbatlas_privatelink_endpoint_service.service.*)
      vpc_endpoint                 = one(aws_vpc_endpoint.service.*)
      security_group               = one(aws_security_group.endpoint.*)
    }
  }
}

module "permanent_record" {
  source = "../../utils/permanent-record"


  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}