# AWS Organizations Resources
# This file manages AWS Organizations including policies, service principals, delegated administrators and related settings.

# Create the organization with service principals and policy types from configuration
resource "aws_organizations_organization" "this" {
  feature_set = local.context.organization.feature_set

  aws_service_access_principals = flatten([
    for category, principals in local.context.organization.service_principals : principals
  ])

  enabled_policy_types = try(local.context.organization.policies.enabled_types, [])
}

locals {
  organization_root_id = aws_organizations_organization.this.roots[0].id

  # Convert list-based service principals to a map for better lookup
  service_principals_map = {
    for idx, principal in aws_organizations_organization.this.aws_service_access_principals :
    replace(principal, ".amazonaws.com", "") => principal
  }

  # Convert policy types to a map for better lookup
  policy_types_map = {
    for idx, type in aws_organizations_organization.this.enabled_policy_types :
    type => true
  }

  # Delegated administrators have been moved to the security workspace
}

# AWS Control Tower is now managed in control_tower.tf using the awscc provider

# Direct application tags
resource "aws_ce_cost_allocation_tag" "direct" {
  for_each = try(local.context.organization.cost_allocation_tags.direct, {})

  status  = try(each.value.status, "Active")
  tag_key = each.key
}

# System tags (CloudFormation, Terraform, etc)
resource "aws_ce_cost_allocation_tag" "system" {
  for_each = {
    for tag_key, tag_config in flatten([
      for system_name, system_config in try(local.context.organization.cost_allocation_tags.system, {}) : [
        for tag_name, tag_value in try(system_config.tags, {}) : {
          key   = "${try(system_config.prefix, "")}${system_config.prefix != "" ? ":" : ""}${tag_name}"
          value = tag_value
        }
      ]
    ]) : tag_key.key => tag_key.value
  }

  status  = try(each.value.status, "Active")
  tag_key = each.key
}

# Service Catalog configuration
resource "aws_servicecatalog_organizations_access" "this" {
  enabled = true

  depends_on = [aws_organizations_organization.this]
}
