module "delivery_stream_ssm_parameters" {
  providers = {
    aws = aws.parameters_store
  }

  source = "./infrastructure-parameters-store"

  infrastructure = local.configured_s3_buckets

  allowlist = [
    "delivery_stream_arn",
    "delivery_stream_name",
  ]

  transparent_ssm_path_prefix = var.transparent_ssm_path_prefix

  ssm_path_prefix = var.ssm_path_prefix

  context = var.context
}

locals {
  delivery_stream_data = {
    s3_buckets = {
      for asset_name, asset_parameters_data in module.delivery_stream_ssm_parameters.ssm_parameters : asset_name => {
        ssm_parameters = asset_parameters_data
      }
    }
  }
}