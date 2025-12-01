locals {
  # Shared configuration for all workspaces
  terraform_workspace_config = {
    providers = [
      "aws",
    ]

    # Standard context binding to get account data
    bind_to_context = {
      state_path = "terraform/state/terraform-aws-organization/workspaces/aggregator/terraform.tfstate"
      state_key  = "context"
    }
  }

  # Define workspaces for baseline services
  base_workspaces = {
    # CloudTrail configuration
    cloudtrail = {
      description = "CloudTrail organization trail"

      bind_to_context = local.default_context_binding
    }

    # Config baseline
    config_baseline = {
      dependencies = ["cloudtrail"]
      description  = "AWS Config baseline configuration"

      bind_to_context = local.default_context_binding
    }

    # CloudWatch Logs
    logs = {
      dependencies = ["cloudtrail"]
      description  = "Centralized logging configuration"

      bind_to_context = local.default_context_binding
    }

    # IAM baseline
    iam = {
      description = "IAM baseline standards"

      bind_to_context = local.default_context_binding
    }

    # Security findings
    findings = {
      dependencies = ["cloudtrail", "logs"]
      description  = "Security findings integration"

      bind_to_context = local.default_context_binding
    }
  }

  extra_workspaces = {
    # Aggregator to collect all outputs
    aggregator = {
      dependencies = keys(local.base_workspaces)
      description  = "Baseline services aggregator"

      bind_to_context = local.default_context_binding
    }
  }

  terraform_workspaces = merge(local.base_workspaces, local.extra_workspaces)

  # Workflow configuration
  terraform_workflow_config = {
    name        = "aws-baseline"
    description = "AWS Organization Baseline Services"
  }

  # Path configuration
  workspaces_dir = "workspaces/aws/baseline"
  rel_to_root    = "../../.."
}

# Pipeline Configuration
module "pipeline" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//terraform/terraform-pipeline"

  workspaces  = local.terraform_workspaces
  workflow    = local.terraform_workflow_config
  save_files  = true
  rel_to_root = local.rel_to_root
} 