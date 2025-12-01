locals {
  gws_workspace_config = merge(local.terraform_workspace_config, {
    root_dir = local.nested_root_dir

    workspace_dir = "gws"

    providers = [
      "googleworkspace",
    ]

    backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "gws")
  })

  gcp_workspace_config = merge(local.terraform_workspace_config, {
    root_dir = local.nested_root_dir

    workspace_dir = "gcp"

    providers = [
      "google",
      "google-beta",
    ]

    backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "gcp")
  })

  terraform_workspaces = {
    org_units = merge(local.gws_workspace_config, {
      extra_files = {
        "main.tf.json" = jsonencode({
          resource = {
            googleworkspace_org_unit = local.org_units_terraform_config
          }
        })
      }
    })

    assignments = local.gws_workspace_config

    policies = local.gcp_workspace_config

    projects = local.gcp_workspace_config


    authentication = merge(local.gcp_workspace_config, {
      provider_overrides = {
        postgresql = {
          source  = "cyrilgdn/postgresql"
          version = "1.25.0"
        }
      }

      providers = [
        "github",
        "google",
        "googleworkspace",
        "snowflake",
      ]

      secrets_kms_key_arn = format("arn:aws:kms:%s:%s:alias/global", local.region, local.account_id)
    })

    functions = local.gcp_workspace_config
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
