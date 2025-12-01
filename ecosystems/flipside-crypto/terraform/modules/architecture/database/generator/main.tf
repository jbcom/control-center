locals {
  networked_accounts_data = var.context["networked_accounts_by_json_key"]

  spokes_data = var.context["networks"]

  global_kms_key_arn = "arn:aws:kms:us-east-1:862006574860:alias/terraform-organization"

  root_account_binding = {
    FlipsideCryptoRoot = ""
  }

  backend_bucket_workspaces_path = "terraform/state/terraform-databases/workspaces"

  terraform_workspace_config = merge(var.base_terraform_workspace_config, {
    root_dir                       = "terraform/workspaces/architecture"
    workspace_dir                  = "database"
    backend_bucket_workspaces_path = local.backend_bucket_workspaces_path
  })

  nested_root_dir          = "${local.terraform_workspace_config["root_dir"]}/${local.terraform_workspace_config["workspace_dir"]}"
  nested_root_dir_template = "${local.nested_root_dir}/%s"

  backend_path_template               = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/%s/terraform.tfstate"
  nested_backend_path_prefix_template = "${local.terraform_workspace_config["backend_bucket_workspaces_path"]}/%s"
  nested_backend_path_template        = "${local.nested_backend_path_prefix_template}/%s/terraform.tfstate"

  record_path          = "records/${local.nested_root_dir}"
  record_path_template = "${local.record_path}/%s"

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

      bind_to_context = merge(var.default_context_binding, {
        config_dir            = "config/infrastructure/database"
        nest_config_under_key = "database_infrastructure"
      })
    })
  }

  infrastructure_workspaces = {
    for json_key, account_data in local.networked_accounts_data : "infrastructure-${json_key}" => merge(local.terraform_workspace_config, {
      root_dir      = format(local.nested_root_dir_template, "infrastructure")
      workspace_dir = "accounts"

      job_name               = "infrastructure-${json_key}"
      workspace_name         = "infrastructure-${json_key}"
      workspace_dir_name     = json_key
      backend_workspace_name = json_key

      dependencies = [
        for _, job_data in local.base_workspaces : job_data["job_name"]
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
        ]))

        ordered_records_merge = false
      })

      extra_files = {
        "main.tf.json" = jsonencode({
          module = {
            base = {
              providers = {
                aws        = "aws"
                "aws.root" = "aws.FlipsideCryptoRoot"
              }

              source = "$${REL_TO_ROOT}/terraform/modules/architecture/database/infrastructure/infrastructure-resources"

              environment = account_data["environment"]

              kms_key_arn = "$${local.context.kms_key_arn}"
              kms_key_id  = "$${local.context.kms_key_arn}"

              secrets_kms_key_arn = local.global_kms_key_arn

              account = account_data

              networking = "$${local.context.networking}"

              infrastructure = "$${local.context.database_infrastructure.${json_key}}"

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
  ssm_parameters_nested_state_path_template = "${local.ssm_parameters_backend_path_template}/ssm-parameters-%s/terraform.tfstate"

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
        "infrastructure-${json_key}",
      ]

      bind_to_account = account_data["execution_role_arn"]

      accounts = local.root_account_binding

      bind_to_context = merge(var.networking_context_bindings[json_key], {
        merge_records = concat(local.required_merge_records[json_key], [
          format(local.record_path_template, "infrastructure/accounts/${json_key}.json"),
        ])

        nest_records_under_key = "database_infrastructure"
      })

      backend_bucket_workspaces_path = format(local.ssm_parameters_backend_path_template, "accounts")
    })
  }

  #  monitoring_workspaces = {
  #    for json_key, account_data in local.networked_accounts_data : "monitoring-${json_key}" => merge(local.terraform_workspace_config, {
  #      root_dir      = local.nested_root_dir
  #      workspace_dir = "monitoring"
  #
  #      job_name               = "monitoring-${json_key}"
  #      workspace_name         = "monitoring-${json_key}"
  #      workspace_dir_name     = json_key
  #      backend_workspace_name = json_key
  #
  #      runner_label = "self-hosted"
  #
  #      dependencies = [
  #        "ssm-parameters-${json_key}",
  #      ]
  #
  #      bind_to_account = account_data["execution_role_arn"]
  #
  #      bind_to_context = merge(var.networking_context_bindings[json_key], {
  #        merge_records = concat(local.required_merge_records[json_key], [
  #          format(local.record_path_template, "ssm-parameters/accounts/${json_key}.json"),
  #        ])
  #
  #        nest_records_under_key = "database_infrastructure"
  #      })
  #
  #      extra_files = {
  #        "main.tf.json" = jsonencode({
  #          module = {
  #            base = {
  #              source = "$${REL_TO_ROOT}/terraform/modules/architecture/database/monitoring"
  #
  #              infrastructure = "$${local.context.database_infrastructure}"
  #
  #              context = "$${local.context}"
  #            }
  #          }
  #        })
  #      }
  #
  #      backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "monitoring")
  #    })
  #  }

  #  mongodb_atlas_extra_files = {
  #    "mongodbatlas.tf.json" = jsonencode({
  #      provider = {
  #        mongodbatlas = [
  #          {
  #            public_key  = "$${local.vendors_data.mongodb_public_key}"
  #            private_key = "$${local.vendors_data.mongodb_private_key}"
  #          }
  #        ]
  #      }
  #    })
  #  }
  #
  #  mongodb_atlas_terraform_workspace_config = merge(local.terraform_workspace_config, {
  #    root_dir      = local.nested_root_dir
  #    workspace_dir = "mongodb-atlas"
  #
  #    providers = [
  #      "googleworkspace",
  #    ]
  #
  #    provider_overrides = {
  #      mongodbatlas = {
  #        source  = "mongodb/mongodbatlas"
  #        version = "1.9.0"
  #      }
  #    }
  #
  #    extra_files = local.mongodb_atlas_extra_files
  #
  #    backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "mongodb-atlas")
  #  })
  #
  #  mongodb_atlas_config = var.context["mongodb_atlas"]
  #  mongodb_atlas_regions = {
  #    for region_data in local.mongodb_atlas_config["networks"]["regions"] : region_data["name"] => lower(replace(region_data["name"], "_", "-"))
  #  }
  #
  #  mongodb_atlas_project_workspaces = {
  #    mongodb-atlas-projects = merge(local.mongodb_atlas_terraform_workspace_config, {
  #      job_name               = "mongodb-atlas-projects"
  #      workspace_dir_name     = "projects"
  #      backend_workspace_name = "projects"
  #
  #      dependencies = []
  #
  #      bind_to_account = local.networked_accounts_data["Transit"]["execution_role_arn"]
  #    })
  #  }
  #
  #  mongodb_atlas_privatelink_workspaces = {
  #    for json_key, spoke_data in local.spokes_data : "mongodb-atlas-privatelink-${json_key}" => merge(local.mongodb_atlas_terraform_workspace_config, {
  #      root_dir      = format("%s/%s", local.mongodb_atlas_terraform_workspace_config["root_dir"], local.mongodb_atlas_terraform_workspace_config["workspace_dir"])
  #      workspace_dir = "privatelink"
  #
  #      workspace_dir_name     = json_key
  #      backend_workspace_name = json_key
  #
  #      job_name = "mongodb-atlas-privatelink-${json_key}"
  #
  #      dependencies = [
  #        for _, job_data in local.mongodb_atlas_project_workspaces : job_data["job_name"]
  #      ]
  #
  #      bind_to_account = local.spokes_data[json_key]["execution_role_arn"]
  #
  #      bind_to_context = merge(var.default_context_binding, {
  #        environment = spoke_data["environment"]
  #        tags        = lookup(spoke_data, "tags", var.context["tags"])
  #
  #        config_dir = format(local.record_path_template, "mongodb-atlas/projects")
  #
  #        nest_config_under_key = "mongodb_atlas_projects"
  #      })
  #
  #      extra_files = merge(local.mongodb_atlas_extra_files, {
  #        "main.tf.json" = jsonencode({
  #          module = {
  #            for region_name, _ in local.mongodb_atlas_regions : region_name => {
  #              source = "$${REL_TO_ROOT}/terraform/modules/mongodb-atlas/mongodb-atlas-aws-privatelink"
  #
  #              mongodb_aws_region = region_name
  #
  #              json_key = json_key
  #
  #              context = "$${local.context}"
  #
  #              records_dir = "records/$${local.workspace_dir}"
  #
  #              records_file_name = "${region_name}.json"
  #
  #              rel_to_root = "$${local.rel_to_root}"
  #            }
  #          }
  #        })
  #      })
  #    })
  #  }
  #
  #  mongodb_atlas_base_workspaces = merge(local.mongodb_atlas_project_workspaces, local.mongodb_atlas_privatelink_workspaces)
  #
  #  mongodb_atlas_cluster_workspaces = {
  #    for region_name, _ in local.mongodb_atlas_regions : "mongodb-atlas-clusters-${region_name}" => merge(local.mongodb_atlas_terraform_workspace_config, {
  #      root_dir      = format("%s/%s", local.mongodb_atlas_terraform_workspace_config["root_dir"], local.mongodb_atlas_terraform_workspace_config["workspace_dir"])
  #      workspace_dir = "clusters"
  #
  #      job_name               = "mongodb-atlas-clusters-${region_name}"
  #      workspace_dir_name     = region_name
  #      backend_workspace_name = region_name
  #
  #      dependencies = [
  #        for _, job_data in local.mongodb_atlas_base_workspaces : job_data["job_name"]
  #      ]
  #
  #      accounts = {
  #        FlipsideCryptoRoot = ""
  #        Transit            = local.networked_accounts_data["Transit"]["execution_role_arn"]
  #      }
  #
  #      bind_to_context = merge(var.default_context_binding, {
  #        merge_record = format(local.record_path_template, "mongodb-atlas/projects/${region_name}.json")
  #
  #        nest_records_under_key = "mongodb_atlas_project"
  #      })
  #
  #      extra_files = merge(local.mongodb_atlas_extra_files, {
  #        "main.tf.json" = jsonencode({
  #          module = {
  #            base = {
  #              source = "$${REL_TO_ROOT}/terraform/modules/mongodb-atlas/mongodb-atlas-cluster"
  #
  #              providers = {
  #                aws        = "aws"
  #                "aws.root" = "aws.FlipsideCryptoRoot"
  #              }
  #
  #              for_each = "$${local.context.databases.mongodb_atlas.clusters}"
  #
  #              cluster_id = "$${each.key}"
  #
  #              mongodb_aws_region = region_name
  #
  #              config = "$${each.value}"
  #
  #              context = "$${local.context}"
  #
  #              records_dir = "records/$${local.workspace_dir}"
  #
  #              records_file_name = "$${each.key}.json"
  #
  #              rel_to_root = "$${local.rel_to_root}"
  #            }
  #          }
  #        })
  #      })
  #    })
  #  }
  #
  #  mongodb_atlas_workspaces = merge(local.mongodb_atlas_base_workspaces, local.mongodb_atlas_cluster_workspaces)

  extra_workspaces = {
    aggregator = merge(local.terraform_workspace_config, {
      job_name = "aggregator"

      dependencies = concat([
        for _, job_data in local.ssm_parameter_workspaces : job_data["job_name"]
      ])

      bind_to_context = merge(var.default_context_binding, {
        config_dir  = format(local.record_path_template, "ssm-parameters/accounts")
        config_glob = "*.json"

        nest_config_under_key = "database_infrastructure"
      })
    })
  }

  terraform_workspaces = merge(local.base_workspaces, local.infrastructure_workspaces, local.ssm_parameter_workspaces, local.extra_workspaces)
}

module "pipeline" {
  source = "../../../terraform/terraform-pipeline"

  workspaces = local.terraform_workspaces

  workflow = merge(var.base_terraform_workflow_config, {
    workflow_name = "database-architecture"
  })

  save_files = true

  rel_to_root = var.rel_to_root
}