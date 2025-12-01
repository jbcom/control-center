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

  # Default context binding shared across workspaces
  default_context_binding = {
    state_path = "terraform/state/terraform-aws-organization/workspaces/aggregator/terraform.tfstate"
    state_key  = "context"
    config_dir = "workspaces/aws/billing/generator/config" # Updated config path
  }

  # Define workspaces for billing services
  base_workspaces = {
    # CUR configuration (Cost and Usage Reports)
    cur = merge(local.terraform_workspace_config, {
      description = "Cost and Usage Reports configuration"

      bind_to_context = merge(local.default_context_binding, {
        config_files = ["services.yaml"] # Reference to services.yaml config
      })
    })

    # CUDOS dashboards
    cudos = merge(local.terraform_workspace_config, {
      dependencies = ["cur"]
      description  = "CUDOS dashboards for cost optimization"

      bind_to_context = merge(local.default_context_binding, {
        config_files = ["services.yaml"] # Reference to services.yaml config
      })
    })

    # Budget alerts
    budgets = merge(local.terraform_workspace_config, {
      dependencies = ["cur"]
      description  = "Budget alerts and notifications"

      bind_to_context = merge(local.default_context_binding, {
        config_files = ["budgets.yaml"] # Reference to budgets.yaml config
      })
    })

    # Cost allocation tags
    cost_tags = merge(local.terraform_workspace_config, {
      description = "Cost allocation tag management"

      bind_to_context = merge(local.default_context_binding, {
        config_files = ["cost_allocation_tags.yaml"] # Reference to cost_allocation_tags.yaml config
      })
    })

    # Cost optimization recommendations
    cost_optimization = merge(local.terraform_workspace_config, {
      dependencies = ["cur", "cudos"]
      description  = "Cost optimization recommendations"

      bind_to_context = merge(local.default_context_binding, {
        config_files = ["services.yaml"] # Reference to services.yaml config
      })
    })
  }

  extra_workspaces = {
    # Aggregator to collect all outputs
    aggregator = merge(local.terraform_workspace_config, {
      dependencies = keys(local.base_workspaces)
      description  = "Billing services aggregator"

      bind_to_context = merge(local.default_context_binding, {
        config_files = [
          "services.yaml",
          "budgets.yaml",
          "cost_allocation_tags.yaml"
        ] # Reference to all config files
      })
    })
  }

  terraform_workspaces = merge(local.base_workspaces, local.extra_workspaces)

  # Workflow configuration
  terraform_workflow_config = {
    name        = "aws-billing"
    description = "AWS Organization Billing Services"
  }

  # Path configuration
  workspaces_dir = "workspaces/aws/billing"
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