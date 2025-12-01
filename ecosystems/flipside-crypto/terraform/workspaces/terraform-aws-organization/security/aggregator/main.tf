# AWS Security Aggregator Main
# This file aggregates outputs from all security workspaces

# Get data from the delegation workspace
data "terraform_remote_state" "delegation" {
  backend = "s3"
  config = {
    bucket = local.state_bucket
    key    = "terraform/state/terraform-aws-security/workspaces/delegation/terraform.tfstate"
    region = local.region
  }
}

# Get data from the GuardDuty workspace
data "terraform_remote_state" "guardduty" {
  backend = "s3"
  config = {
    bucket = local.state_bucket
    key    = "terraform/state/terraform-aws-security/workspaces/guardduty/terraform.tfstate"
    region = local.region
  }
}

# Get data from the SecurityHub workspace
data "terraform_remote_state" "securityhub" {
  backend = "s3"
  config = {
    bucket = local.state_bucket
    key    = "terraform/state/terraform-aws-security/workspaces/securityhub/terraform.tfstate"
    region = local.region
  }
}

# Get data from the Macie workspace
data "terraform_remote_state" "macie" {
  backend = "s3"
  config = {
    bucket = local.state_bucket
    key    = "terraform/state/terraform-aws-security/workspaces/macie/terraform.tfstate"
    region = local.region
  }
}

locals {
  # Get region and state bucket from the context
  region       = local.context.aws.region
  state_bucket = local.context.aws.state_bucket

  # Collect outputs for permanent record
  records_config = {
    # Delegated administrators
    delegated_administrators            = try(data.terraform_remote_state.delegation.outputs.delegated_administrators, {})
    delegated_administrators_by_service = try(data.terraform_remote_state.delegation.outputs.delegated_administrators_by_service, {})

    # Security services
    security_services = {
      guardduty   = try(data.terraform_remote_state.guardduty.outputs.guardduty, {})
      securityhub = try(data.terraform_remote_state.securityhub.outputs.securityhub, {})
      macie       = try(data.terraform_remote_state.macie.outputs.macie, {})
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}

# Export aggregated security configuration for record generation
output "delegated_administrators" {
  description = "Organization delegated administrators"
  value       = try(data.terraform_remote_state.delegation.outputs.delegated_administrators, {})
}

output "delegated_administrators_by_service" {
  description = "Organization delegated administrators by service"
  value       = try(data.terraform_remote_state.delegation.outputs.delegated_administrators_by_service, {})
}

output "security_services" {
  description = "Security services configuration"
  value = {
    guardduty   = try(data.terraform_remote_state.guardduty.outputs.guardduty, {})
    securityhub = try(data.terraform_remote_state.securityhub.outputs.securityhub, {})
    macie       = try(data.terraform_remote_state.macie.outputs.macie, {})
  }
}
