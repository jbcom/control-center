locals {
  accounts_data          = var.context["accounts_by_json_key"]
  security_accounts_data = var.context["security_accounts_by_json_key"]

  security_accounts_execution_role_arn_map = {
    for json_key, account_data in local.security_accounts_data : json_key => account_data["execution_role_arn"]
  }

  member_accounts_data = {
    for json_key, account_data in local.accounts_data : json_key => account_data if json_key != "Audit"
  }

  member_accounts_execution_role_arn_map = {
    for json_key, account_data in local.member_accounts_data : json_key => account_data["execution_role_arn"]
  }

  networked_accounts_by_json_key = var.context["networked_accounts_by_json_key"]
  networked_accounts_by_id       = var.context["networked_accounts"]

  networked_accounts_data    = var.context["networked_accounts_by_json_key"]
  architecture_accounts_data = var.context["architecture_accounts_by_json_key"]

  backend_bucket_workspaces_path = "terraform/state/terraform-aws-architecture/workspaces"

  terraform_workspace_config = merge(var.base_terraform_workspace_config, {
    root_dir                       = "terraform/workspaces"
    workspace_dir                  = "architecture"
    backend_bucket_workspaces_path = local.backend_bucket_workspaces_path
  })

  nested_root_dir          = "${local.terraform_workspace_config["root_dir"]}/${local.terraform_workspace_config["workspace_dir"]}"
  nested_root_dir_template = "${local.nested_root_dir}/%s"

  backend_path_template               = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/%s/terraform.tfstate"
  nested_backend_path_prefix_template = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/%s"
  nested_backend_path_template        = "${local.nested_backend_path_prefix_template}/%s/terraform.tfstate"

  record_path          = "records/${local.nested_root_dir}"
  record_path_template = "${local.record_path}/%s"

  base_workspaces = {
    resources = merge(local.terraform_workspace_config, {
      job_name = "resources"

      dependencies = []
    })

    docs = merge(local.terraform_workspace_config, {
      job_name = "docs"

      dependencies = [
        "resources",
      ]

      bind_to_context = merge(var.default_context_binding, {
        merge_record = format(local.record_path_template, "resources.json")
      })
    })
  }

  guardduty_configuration = {
    "management_acc_id" : local.account_id,
    "delegated_admin_acc_id" : local.security_accounts_data["Audit"]["account_id"],
    "logging_acc_id" : local.security_accounts_data["LogArchive"]["account_id"],
    "target_regions" : join(",", local.supported_regions),
    "organization_id" : var.context["organization"]["aws"]["id"],
    "default_region" : local.region,
    "role_to_assume_for_role_creation" : "AWSGuardDutyExecution",
    "finding_publishing_frequency" : "FIFTEEN_MINUTES",
    "guardduty_findings_bucket_region" : local.region,
    "logging_acc_s3_bucket_name" : "flipsidecrypto-guardduty-logs",
    "security_acc_kms_key_alias" : "guardduty",
    "s3_access_log_bucket_name" : try(jsondecode(file(var.networking_record_files["FlipsideCryptoRoot"]))["access_logs"]["bucket_id"], ""),
    "tfm_state_backend_s3_bucket" : local.terraform_workspace_config["backend_bucket_name"],
    "tfm_state_backend_dynamodb_table" : local.terraform_workspace_config["backend_dynamodb_table"]
  }

  guardduty_workspace_config = merge(local.terraform_workspace_config, {
    root_dir      = local.nested_root_dir
    workspace_dir = "guardduty"

    backend_bucket_workspaces_path = "terraform/state/terraform-aws-guardduty/workspaces"
  })

  guardduty_role_workspace_config = merge(local.guardduty_workspace_config, {
    root_dir      = "${local.guardduty_workspace_config["root_dir"]}/${local.guardduty_workspace_config["workspace_dir"]}"
    workspace_dir = "roles"
  })

  guardduty_base_workspaces = merge({
    guardduty-role-Management = merge(local.guardduty_role_workspace_config, {
      workspace_dir_name = "Management"

      job_name = "guardduty-role-Management"

      dependencies = [
        for _, job_data in local.base_workspaces : job_data["job_name"]
      ]

      bind_to_context = var.default_context_binding
    })
    }, {
    for json_key, execution_role_arn in local.security_accounts_execution_role_arn_map : "guardduty-role-${json_key}" => merge(local.guardduty_role_workspace_config, {
      workspace_dir_name = json_key

      job_name = "guardduty-role-${json_key}"

      dependencies = [
        for _, job_data in local.base_workspaces : job_data["job_name"]
      ]

      bind_to_account = execution_role_arn

      bind_to_context = var.default_context_binding

      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            role = {
              source = "$${REL_TO_ROOT}/terraform/modules/aws/aws-guardduty/aws-guardduty-stack-deployment"

              stack_name = "guardduty-${json_key}-account-role"

              stack_capabilities = [
                "CAPABILITY_NAMED_IAM",
              ]

              template_name = "role-to-assume-for-role-creation"

              context = "$${local.context}"

              records_dir = "records/$${local.workspaces_dir}"

              records_file_name = "${json_key}.json"

              rel_to_root = "$${local.rel_to_root}"
            }
          }
        })
      }
    })
  })

  guardduty_extra_workspaces = {
    guardduty-roles-aggregator = merge(local.guardduty_workspace_config, {
      job_name = "guardduty-roles-aggregator"

      workspace_dir_name = "aggregator"

      dependencies = keys(local.guardduty_base_workspaces)

      accounts = local.security_accounts_execution_role_arn_map

      bind_to_context = merge(var.default_context_binding, {
        config_dir = format(local.record_path_template, "guardduty/roles")

        nest_config_under_key = "guardduty_roles"
      })
    })

    guardduty-deployment = merge(local.guardduty_workspace_config, {
      job_name = "guardduty-deployment"

      workspace_dir_name = "deployment"

      dependencies = [
        "guardduty-roles-aggregator",
      ]

      accounts = local.security_accounts_execution_role_arn_map

      bind_to_context = merge(var.default_context_binding, {
        merge_record = format(local.record_path_template, "guardduty/aggregator.json")
      })
    })
  }

  guardduty_workspaces = merge(local.guardduty_base_workspaces, local.guardduty_extra_workspaces)

  ram_shares_backend_path                        = "terraform/state/terraform-aws-ram/workspaces"
  ram_shares_backend_path_template               = "${local.ram_shares_backend_path}/%s/terraform.tfstate"
  ram_shares_nested_backend_path_prefix_template = "${local.ram_shares_backend_path}/%s"
  ram_shares_nested_backend_path_template        = "${local.ram_shares_nested_backend_path_prefix_template}/%s/terraform.tfstate"

  ram_shares = {
    for json_key, _ in local.networked_accounts_by_json_key : json_key => lookup(var.context["ram_shares"], json_key, {})
  }

  ram_share_workspaces = {
    for json_key, account_data in local.networked_accounts_by_json_key : "ram-shares-${json_key}" => merge(local.terraform_workspace_config, {
      root_dir           = local.nested_root_dir
      workspace_dir      = "ram-shares"
      workspace_dir_name = json_key

      job_name = "ram-shares-${json_key}"

      dependencies = [
        for _, job_data in local.base_workspaces : job_data["job_name"]
      ]

      bind_to_account = account_data["execution_role_arn"]

      bind_to_context = merge(var.default_context_binding, {
        environment = account_data["environment"]
      })

      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              source = "$${REL_TO_ROOT}/terraform/modules/aws/aws-ram/aws-ram-shares"

              context = "$${local.context}"

              records_dir = "records/$${local.workspaces_dir}"

              records_file_name = "${json_key}.json"

              rel_to_root = "$${local.rel_to_root}"
            }
          }
        })
      }

      backend_bucket_workspaces_path = format(local.ram_shares_nested_backend_path_prefix_template, "ram-shares")
    })
  }

  ram_association_workspaces = {
    for json_key, account_data in local.networked_accounts_by_json_key : "ram-associations-${json_key}" => merge(local.terraform_workspace_config, {
      root_dir           = local.nested_root_dir
      workspace_dir      = "ram-associations"
      workspace_dir_name = json_key

      job_name = "ram-associations-${json_key}"

      dependencies = [
        "ram-shares-${json_key}",
      ]

      bind_to_account = account_data["execution_role_arn"]

      bind_to_context = merge(var.default_context_binding, {
        environment = account_data["environment"]

        merge_records = formatlist(local.record_path_template, [
          "resources.json",
          "ram-shares/${json_key}.json",
        ])
      })

      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              source = "$${REL_TO_ROOT}/terraform/modules/aws/aws-ram/aws-ram-associations"

              config = "$${local.context.ram_shares.${json_key}}"

              infrastructure = "$${local.context.infrastructure.${json_key}}"

              context = "$${local.context}"
            }
          }
        })
      }


      backend_bucket_workspaces_path = format(local.ram_shares_nested_backend_path_prefix_template, "ram-associations")
    })
  }

  ram_workspaces = merge(local.ram_share_workspaces, local.ram_association_workspaces)

  terraform_workspaces = merge(local.base_workspaces, local.guardduty_workspaces, local.ram_workspaces)
}

module "pipeline" {
  source = "../../terraform/terraform-pipeline"

  workspaces = local.terraform_workspaces

  workflow = merge(var.base_terraform_workflow_config, {
    workflow_name = "architecture"
  })

  save_files = true

  rel_to_root = var.rel_to_root
}