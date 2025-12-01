data "aws_organizations_organization" "current" {}

locals {
  organization_id = data.aws_organizations_organization.current.id

  s3_buckets_unmanaged_config = {
    for name, data in local.s3_buckets_base_config : name => data if !data["managed"]
  }
}

data "aws_s3_bucket" "unmanaged_s3_bucket" {
  for_each = local.s3_buckets_unmanaged_config

  bucket = each.key
}

locals {
  unmanaged_s3_bucket_data = {
    for bucket_name, bucket_data in data.aws_s3_bucket.unmanaged_s3_bucket : bucket_name => merge(local.s3_buckets_unmanaged_config[bucket_name], {
      bucket_domain_name          = bucket_data["bucket_domain_name"]
      bucket_regional_domain_name = bucket_data["bucket_regional_domain_name"]
      bucket_website_domain       = ""
      bucket_website_endpoint     = ""
      bucket_id                   = bucket_data["id"]
      bucket_arn                  = bucket_data["arn"]
      bucket_region               = bucket_data["region"]
      enabled                     = true
      user_enabled                = false
      user_name                   = ""
      user_arn                    = ""
      user_unique_id              = ""
      replication_role_arn        = ""
      access_key_id               = ""
      secret_access_key           = ""
      access_key_id_ssm_path      = ""
      secret_access_key_ssm_path  = ""
    })
  }
}