locals {
  tags = local.context.tags

  record_path          = "records/${local.nested_root_dir}"
  record_path_template = "${local.record_path}/%s.json"

  base_workspaces = {
    organization = merge(local.terraform_workspace_config, {
      disable_vendors_module = true

      providers = [
        "github",
      ]

      provider_overrides = {
        awscc = {
          source  = "hashicorp/awscc"
          version = "1.37.0"
        }

        controltower = {
          source  = "CLDZE/controltower"
          version = "1.3.6"
        }
      }

      bind_to_context = merge(local.default_context_binding, {
        merge_record = format(local.record_path_template, "generator")
      })
    })

    authentication = merge(local.terraform_workspace_config, {
      dependencies = [
        "organization",
      ]

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
      ]

      secrets_kms_key_arn = format("arn:aws:kms:%s:%s:alias/global", local.region, local.account_id)

      bind_to_context = merge(local.default_context_binding, {
        merge_record = format(local.record_path_template, "organization")
      })
    })

    bots = merge(local.terraform_workspace_config, {
      dependencies = [
        "authentication",
      ]

      bind_to_context = merge(local.default_context_binding, {
        merge_record = format(local.record_path_template, "authentication")
      })
    })

    secrets = merge(local.terraform_workspace_config, {
      dependencies = [
        "authentication",
      ]

      providers = [
        "doppler",
        "github",
      ]

      bind_to_context = merge(local.default_context_binding, {
        merge_record = format(local.record_path_template, "bots")
      })
    })

    sso = merge(local.terraform_workspace_config, {
      dependencies = ["organization"]

      providers = [
        "googleworkspace",
      ]

      bind_to_context = merge(local.default_context_binding, {
        merge_record = format(local.record_path_template, "organization")
      })
    })
  }

  extra_workspaces = {
    guards = merge(local.terraform_workspace_config, {
      dependencies = [
        "organization",
        "bots",
      ]

      bind_to_context = merge(local.default_context_binding, {
        merge_records = formatlist(local.record_path_template, [
          "generator",
          "organization",
          "bots",
        ])
      })
    })

    aggregator = merge(local.terraform_workspace_config, {
      dependencies = keys(local.base_workspaces)

      bind_to_context = merge(local.default_context_binding, {
        merge_records = formatlist(local.record_path_template, keys(local.base_workspaces))
      })
    })
  }

  terraform_workspaces = merge(local.base_workspaces, local.extra_workspaces)
}

module "pipeline" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//terraform/terraform-pipeline"

  workspaces  = local.terraform_workspaces
  workflow    = local.terraform_workflow_config
  save_files  = true
  rel_to_root = local.rel_to_root
}

locals {
  records_config = merge({
    for k, v in local.context : k => v
    if contains(["guards", "organization", "permission_sets", "policies", "sso"], k)
    }, {
    units         = local.units
    accounts      = local.accounts
    control_tower = local.final_control_tower
  })
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspace_dir}"

  log_file_name = "permanent_record.log"
}
