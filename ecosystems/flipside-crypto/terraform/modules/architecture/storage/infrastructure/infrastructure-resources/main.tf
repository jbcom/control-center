locals {
  vault_path_prefix = "infrastructure/${local.json_key}"

  environment = var.environment != null ? var.environment : lookup(var.context, "environment", null)

  json_key = var.account.json_key

  execution_role_arn = var.account.execution_role_arn

  domain = var.account.domain

  subdomain = var.account.subdomain

  kms_key_arn = var.kms_key_arn
  kms_key_id  = var.kms_key_id

  secrets_kms_key_arn = coalesce(var.secrets_kms_key_arn, local.kms_key_arn)

  vpc_id             = var.networking.vpc_id
  vpc_cidr_block     = var.networking.vpc_cidr_block
  public_subnet_ids  = var.networking.public_subnet_ids
  private_subnet_ids = var.networking.private_subnet_ids

  allowed_cidr_blocks = var.allowed_cidr_blocks.private

  tags = {
    for k, v in var.context["tags"] : k => v if k != "Name"
  }

  public_cidr_blocks = var.allowed_cidr_blocks.public

  public_security_group_rules = [
    {
      type        = "ingress"
      from_port   = 0
      to_port     = 65535
      protocol    = "tcp"
      cidr_blocks = local.public_cidr_blocks
    }
  ]

  private_security_group_rules = [
    for cidr_block in local.allowed_cidr_blocks : {
      type        = "ingress"
      from_port   = 0
      to_port     = 65535
      protocol    = "tcp"
      cidr_blocks = [cidr_block]
    }
  ]

  required_component_data = {
    account_id         = local.account_id
    execution_role_arn = local.execution_role_arn
  }

  live_infrastructure_data = {
    access_logs = local.configured_access_logs

    efs_filesystems = local.configured_efs_filesystems

    s3_buckets = local.configured_s3_buckets

  }
}

module "infrastructure_data" {
  source = "../../../../../../terraform/modules/utils/deepmerge"

  source_maps = [
    local.live_infrastructure_data,
    local.legacy_resources_data,
    local.unmanaged_resources_data,
    local.delivery_stream_private_data,
    local.delivery_stream_public_data,
    local.datasync_private_data,
    local.datasync_public_data,
    local.unmanaged_bucket_delivery_stream_data,
    local.unmanaged_bucket_datasync_data,
  ]
}

locals {
  provisioned_infrastructure_data = module.infrastructure_data.merged_maps
}

module "permanent_record" {
  source = "../../../../../../terraform/modules/utils/permanent-record"

  save_permanent_record = var.save_permanent_record

  records = local.provisioned_infrastructure_data

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}
