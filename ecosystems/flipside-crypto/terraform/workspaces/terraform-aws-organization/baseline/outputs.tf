# Collect outputs for permanent record
locals {
  records_config = {
    baseline = {
      cloudtrail = {
        name                          = aws_cloudtrail.organization.name
        s3_bucket                     = aws_cloudtrail.organization.s3_bucket_name
        include_global_service_events = aws_cloudtrail.organization.include_global_service_events
        is_organization_trail         = aws_cloudtrail.organization.is_organization_trail
      }

      security_services = try(local.context.delegation.security_services, {})
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
} 