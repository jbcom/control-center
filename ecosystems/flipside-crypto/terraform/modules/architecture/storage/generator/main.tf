locals {
  networked_accounts_data    = var.context["networked_accounts_by_json_key"]
  architecture_accounts_data = var.context["architecture_accounts_by_json_key"]

  backend_bucket_workspaces_path = "terraform/state/storage-architecture/workspaces"

  terraform_workspace_config = merge(var.base_terraform_workspace_config, {
    root_dir                       = "terraform/workspaces/architecture"
    workspace_dir                  = "storage"
    backend_bucket_workspaces_path = local.backend_bucket_workspaces_path
  })

  nested_root_dir          = "${local.terraform_workspace_config["root_dir"]}/${local.terraform_workspace_config["workspace_dir"]}"
  nested_root_dir_template = "${local.nested_root_dir}/%s"

  backend_path_template               = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/%s/terraform.tfstate"
  nested_backend_path_prefix_template = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/%s"
  nested_backend_path_template        = "${local.nested_backend_path_prefix_template}/%s/terraform.tfstate"

  record_path          = "records/${local.nested_root_dir}"
  record_path_template = "${local.record_path}/%s"

  root_account_binding = {
    FlipsideCryptoRoot = ""
  }

  required_merge_records = {
    for json_key, context_binding in var.networking_context_bindings : json_key => context_binding["merge_records"]
  }

  base_workspaces = {
    infrastructure-config = merge(local.terraform_workspace_config, {
      root_dir      = local.nested_root_dir
      workspace_dir = "infrastructure"

      job_name = "infrastructure-config"

      workspace_dir_name     = "config"
      backend_workspace_name = "config"

      dependencies = []

      accounts = {
        for account_json_key, account_data in local.architecture_accounts_data : account_json_key => account_data["execution_role_arn"]
      }

      extra_files = {
        "canonical_user_ids.tf.json" = jsonencode({
          data = {
            aws_canonical_user_id = {
              for account_json_key, account_data in local.architecture_accounts_data : account_json_key => {
                provider = "aws.${account_json_key}"
              }
            }
          }

          locals = {
            canonical_user_ids = {
              for account_json_key, account_data in local.architecture_accounts_data : account_json_key => "$${data.aws_canonical_user_id.${account_json_key}.id}"
            }
          }
        })
      }

      bind_to_context = merge(var.default_context_binding, {
        config_dir            = "config/infrastructure/storage"
        nest_config_under_key = "storage_infrastructure"
      })
    })

    legacy-infrastructure = merge(local.terraform_workspace_config, {
      job_name = "legacy-infrastructure"

      dependencies = []
    })
  }

  precursor_workspaces = {
    for json_key, account_data in local.networked_accounts_data : "${json_key}-precursors" => merge(local.terraform_workspace_config, {
      root_dir      = format(local.nested_root_dir_template, "precursors")
      workspace_dir = "accounts"

      job_name               = "${json_key}-precursors"
      workspace_name         = "${json_key}-precursors"
      workspace_dir_name     = json_key
      backend_workspace_name = json_key

      dependencies = [
        for _, job_data in local.base_workspaces : job_data["job_name"]
      ]

      bind_to_account = account_data["execution_role_arn"]

      accounts = merge(local.root_account_binding, {
        (json_key) = account_data["execution_role_arn"]
      })

      bind_to_context = merge(var.networking_context_bindings[json_key], {
        merge_records = concat(local.required_merge_records[json_key], formatlist(local.record_path_template, [
          "infrastructure/config.json",
          "legacy-infrastructure.json",
        ]))
      })

      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              providers = {
                aws        = "aws"
                "aws.root" = "aws.FlipsideCryptoRoot"
              }

              source = "$${REL_TO_ROOT}/terraform/modules/storage/infrastructure/infrastructure-precursors"

              environment = account_data["environment"]

              infrastructure = "$${local.context.storage_infrastructure.${json_key}}"

              context = "$${local.context}"

              records_dir = "records/$${local.workspaces_dir}"

              records_file_name = "${json_key}.json"

              rel_to_root = "$${local.rel_to_root}"
            }
          }
        })
      }

      backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "precursors")
    })
  }

  infrastructure_workspaces = {
    for json_key, account_data in local.networked_accounts_data : "${json_key}-infrastructure" => merge(local.terraform_workspace_config, {
      root_dir      = format(local.nested_root_dir_template, "infrastructure")
      workspace_dir = "accounts"

      job_name               = "${json_key}-infrastructure"
      workspace_name         = "${json_key}-infrastructure"
      workspace_dir_name     = json_key
      backend_workspace_name = json_key

      dependencies = [
        for _, job_data in local.precursor_workspaces : job_data["job_name"]
      ]

      providers = [
        "github",
        "vault",
      ]

      bind_to_account = account_data["execution_role_arn"]

      accounts = merge(local.root_account_binding, {
        (json_key) = account_data["execution_role_arn"]
      })

      bind_to_context = merge(var.networking_context_bindings[json_key], {
        merge_records = concat(local.required_merge_records[json_key], formatlist(local.record_path_template, [
          "infrastructure/config.json",
          "precursors/accounts/${json_key}.json",
          "legacy-infrastructure.json",
        ]))
      })

      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              providers = {
                aws        = "aws"
                "aws.root" = "aws.FlipsideCryptoRoot"
              }

              source = "$${REL_TO_ROOT}/terraform/modules/storage/infrastructure/infrastructure-resources"

              environment = account_data["environment"]

              kms_key_arn = "$${local.context.kms_key_arn}"
              kms_key_id  = "$${local.context.kms_key_arn}"

              account = account_data

              networking = "$${local.context.networking}"

              infrastructure = "$${local.context.storage_infrastructure.${json_key}}"

              context = "$${local.context}"

              records_dir = "records/$${local.workspaces_dir}"

              records_file_name = "${json_key}.json"

              rel_to_root = "$${local.rel_to_root}"
            }
          }
        })
      }

      backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "infrastructure")
    })
  }

  ssm_parameters_backend_path               = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/ssm-parameters"
  ssm_parameters_backend_path_template      = "${local.ssm_parameters_backend_path}/%s"
  ssm_parameters_state_path_template        = "${local.ssm_parameters_backend_path_template}/terraform.tfstate"
  ssm_parameters_nested_state_path_template = "${local.ssm_parameters_backend_path_template}/%s/terraform.tfstate"

  ssm_parameters_workspace_config = merge(local.terraform_workspace_config, {
    backend_bucket_workspaces_path = local.ssm_parameters_backend_path
  })

  ssm_parameter_workspaces = {
    for json_key, account_data in local.networked_accounts_data : "ssm-parameters-${json_key}" => merge(local.terraform_workspace_config, {
      root_dir      = format(local.nested_root_dir_template, "ssm-parameters")
      workspace_dir = "accounts"

      job_name = "ssm-parameters-${json_key}"

      workspace_dir_name = json_key

      dependencies = [
        for _, job_data in local.infrastructure_workspaces : job_data["job_name"]
      ]

      bind_to_account = account_data["execution_role_arn"]

      accounts = local.root_account_binding

      bind_to_context = merge(var.default_context_binding, {
        merge_records = formatlist(local.record_path_template, [
          "infrastructure/accounts/${json_key}.json",
        ])

        nest_records_under_key = "storage_infrastructure"
      })

      backend_bucket_workspaces_path = format(local.ssm_parameters_backend_path_template, "accounts")
    })
  }

  extra_workspaces = {
    aggregator = merge(local.terraform_workspace_config, {
      job_name = "aggregator"

      dependencies = concat([
        for _, job_data in local.ssm_parameter_workspaces : job_data["job_name"]
      ])

      bind_to_context = merge(var.default_context_binding, {
        config_dir  = format(local.record_path_template, "ssm-parameters/accounts")
        config_glob = "*.json"

        nest_config_under_key = "storage_infrastructure"
      })
    })
  }

  terraform_workspaces = merge(local.base_workspaces, local.precursor_workspaces, local.infrastructure_workspaces, local.ssm_parameter_workspaces, local.extra_workspaces)
}

module "pipeline" {
  source = "../../../terraform/terraform-pipeline"

  workspaces = local.terraform_workspaces

  workflow = merge(var.base_terraform_workflow_config, {
    workflow_name = "storage-architecture"
  })

  save_files = true

  rel_to_root = var.rel_to_root
}
