locals {
  # Define workspaces for security services management
  base_workspaces = {
    # Delegated admin configuration for security services
    delegation = {
      description = "Security service delegated administrators"

      bind_to_context = local.default_context_binding
    }

    # GuardDuty specific configuration
    guardduty = {
      dependencies = ["delegation"]
      description  = "GuardDuty configuration across organization"

      bind_to_context = local.default_context_binding
    }

    # SecurityHub specific configuration
    securityhub = {
      dependencies = ["delegation"]
      description  = "SecurityHub standards and controls"

      bind_to_context = local.default_context_binding
    }

    # Macie specific configuration
    macie = {
      dependencies = ["delegation"]
      description  = "Macie sensitive data discovery"

      bind_to_context = local.default_context_binding
    }

    # AWS Config specific configuration
    config = {
      dependencies = ["delegation"]
      description  = "AWS Config rules and remediation"

      bind_to_context = local.default_context_binding
    }
  }

  extra_workspaces = {
    # Aggregator to collect all outputs
    aggregator = {
      dependencies = keys(local.base_workspaces)
      description  = "Security services aggregator"

      bind_to_context = local.default_context_binding
    }
  }

  terraform_workspaces = {
    for workspace_name, workspace_config in merge(local.base_workspaces, local.extra_workspaces) : workspace_name => merge(local.terraform_workspace_config, workspace_config)
  }
}

# Pipeline Configuration
module "pipeline" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//terraform/terraform-pipeline"

  workspaces  = local.terraform_workspaces
  workflow    = local.terraform_workflow_config
  save_files  = true
  rel_to_root = local.rel_to_root
} 