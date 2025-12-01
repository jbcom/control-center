# AWS Policies Main
# This file serves as the entry point for the policies workspace

# AWS Organizations Policies
# Will handle SCP, Tag, Backup, and AI Services policies

# Default policy attachments
resource "aws_organizations_policy_attachment" "ai_services" {
  policy_id = aws_organizations_policy.ai_services.id
  target_id = data.aws_organizations_organization.this.roots[0].id

  depends_on = [data.aws_organizations_organization.this]
}

resource "aws_organizations_policy" "ai_services" {
  name = try(local.context.organization.policies.defaults.ai_services.name, "AI Services Opt Out Policy")
  type = "AISERVICES_OPT_OUT_POLICY"

  content = jsonencode(try(local.context.organization.policies.defaults.ai_services.content, {
    services = {
      default = {
        "opt_out_policy" = {
          "_assign" = "optOut"
        }
      }
    }
  }))

  depends_on = [data.aws_organizations_organization.this]
}

# Get the AWS Organizations resource
data "aws_organizations_organization" "this" {}

locals {
  # Collect outputs for permanent record
  records_config = {
    policies = {
      # AI Services policy
      ai_services = try(aws_organizations_policy.ai_services, null)

      # To be populated with actual policies
      service_control_policies = {}
      tag_policies             = {}
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}

# Export policies for record generation
output "policies" {
  description = "AWS Organizations policies"
  value = {
    # AI Services policy
    ai_services = aws_organizations_policy.ai_services

    # To be populated with actual policies
    service_control_policies = {}
    tag_policies             = {}
  }
}
