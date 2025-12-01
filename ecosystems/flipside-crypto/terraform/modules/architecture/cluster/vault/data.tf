data "aws_region" "current" {}

locals {
  region = data.aws_region.current.name
}

module "dynamodb_table_data" {
  source = "git@github.com:FlipsideCrypto/terraform-aws-architecture.git//modules/infrastructure-metadata"

  category_name = "dynamodb_tables"

  matchers = {
    short_name = "vault-backend"
  }

  context = var.context
}

module "s3_bucket_data" {
  source = "git@github.com:FlipsideCrypto/terraform-aws-architecture.git//modules/infrastructure-metadata"

  category_name = "s3_buckets"

  matchers = {
    short_name = "fsc-vault-backend"
  }

  context = var.context
}

locals {
  dynamodb_table_data = module.dynamodb_table_data.asset
  dynamodb_table_arn  = local.dynamodb_table_data["table_arn"]
  dynamodb_table_name = local.dynamodb_table_data["table_name"]

  s3_bucket_data = module.s3_bucket_data.asset
  s3_bucket_arn  = local.s3_bucket_data["bucket_arn"]
  s3_bucket_id   = local.s3_bucket_data["bucket_id"]
}

data "sops_file" "ca_certificate" {
  source_file = "${var.secrets_dir}/ca.pem"

  input_type = "raw"
}

data "sops_file" "certificate" {
  source_file = "${var.secrets_dir}/tls.crt"

  input_type = "raw"
}

locals {
  ca_certificate_data = data.sops_file.ca_certificate.raw
  certificate_data    = data.sops_file.certificate.raw
}