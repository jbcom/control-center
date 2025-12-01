locals {
  compass_account = local.context["accounts_by_json_key"]["Compass"]
}

module "sso_roles_data" {
  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/aws/aws-sso-roles-data"
}

locals {
  sso_roles = module.sso_roles_data.roles
  grantees = concat(values(local.sso_roles), local.context["admin_bot_users"], [
    local.compass_account["execution_role_arn"]
  ])
}

module "kms" {
  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/aws/aws-kms-key"

  kms_key_name = "compass"

  account_ids = [
    local.account_id,
    local.compass_account["account_id"],
  ]

  grantees = local.grantees

  tags = local.context["tags"]
}

module "compass_assume_role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.19.0"

  attributes = ["compass-assume"]

  enabled = true

  policy_description = "Allow compass account to assume this role"
  role_description   = "Role for compass account to assume"

  principals = {
    AWS = concat(local.grantees, ["arn:aws:iam::${local.compass_account["account_id"]}:root"])
  }

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AdministratorAccess",
  ]

  policy_document_count = 0

  context = local.context
}

locals {
  tags              = local.context["tags"]
  live_environments = local.context["live_environments"]

  copilot_tags = merge(local.tags, {
    copilot-application = "compass",
  })

  copilot_environment_tags = {
    for environment_name in local.live_environments : environment_name => merge(local.copilot_tags, {
      Environment         = environment_name
      copilot-environment = environment_name
    })
  }

  database_monitoring_workspaces = {
    for environment_name, copilot_tags in local.copilot_environment_tags : "database-monitoring-${environment_name}" =>
    merge(local.terraform_workspace_config, {
      root_dir               = local.nested_root_dir
      workspace_dir          = "database-monitoring"
      workspace_dir_name     = environment_name
      backend_workspace_name = environment_name

      provider_overrides = {
        postgresql = {
          source  = "cyrilgdn/postgresql"
          version = "1.24.0"
        }
      }

      providers = [
        "doppler",
      ]

      bind_to_account = local.compass_account["execution_role_arn"]

      bind_to_context = merge(local.default_context_binding, {
        environment = environment_name
      })

      extra_files = {
        "postgresql.tf.json" = jsonencode({
          data = {
            doppler_secrets = {
              this = {
                config  = "${environment_name}_copilot"
                project = "compass"
              }
            }
          }

          locals = {
            # Double $$ escapes `${}` interpolation in Terraform templates
            database_url = "$${data.doppler_secrets.this.map.DATABASE_URL}"

            # Escaped regex pattern in the regexall function
            db_parts          = "$${regexall(\"postgres://(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\\\\d+)/(?P<database>[^?]+)\", local.database_url)[0]}"
            database_name     = "$${local.db_parts.database}"
            database_host     = "$${local.db_parts.host}"
            database_port     = "$${tonumber(local.db_parts.port)}"
            database_username = "$${local.db_parts.username}"

            records_config = {
              database_name       = "$${local.database_name}"
              database_host       = "$${local.database_host}"
              database_port       = "$${local.database_port}"
              database_username   = "$${local.database_username}"
              database_monitoring = "$${module.base}"
            }
          }

          provider = {
            postgresql = [
              {
                scheme    = "awspostgres"
                host      = "$${local.database_host}"
                port      = "$${local.database_port}"
                database  = "$${local.database_name}"
                username  = "$${local.database_username}"
                password  = "$${local.db_parts.password}"
                sslmode   = "require"
                superuser = false
              }
            ]
          }
        })

        "main.tf.json" = jsonencode({
          module = {
            base = {
              source = "$${REL_TO_ROOT}/terraform/modules/database_monitoring"

              database_name = "$${local.database_name}"

              context = "$${local.context}"
            }

            permanent_records = {
              source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/utils/permanent-record"

              records = "$${local.records_config}"

              records_dir = "records/$${local.workspaces_dir}"
            }
          }
        })

        "imports.tf.json" = jsonencode({
          import = [
            {
              id = "datadog"
              to = "module.base.postgresql_role.datadog_role"
              }, {
              id = "Compass${title(environment_name)}.datadog.explain_statement(text)"
              to = "module.base.postgresql_function.datadog_explain_statement"
            }
          ]
        })
      }

      backend_bucket_workspaces_path = format(local.nested_backend_path_prefix_template, "database-monitoring")
    })
  }

  infrastructure_workspaces = {
    infrastructure = merge(local.terraform_workspace_config, {
      dependencies = keys(local.database_monitoring_workspaces)

      providers = [
        "cloudflare",
        "datadog",
        "doppler",
      ]

      bind_to_account = local.compass_account["execution_role_arn"]

      bind_to_context = merge(local.default_context_binding, {
        name        = "compass"
        environment = local.compass_account["environment"]

        config_dir            = "records/terraform/database-monitoring"
        nest_config_under_key = "compass_databases"
      })
    })

    post-processing = merge(local.terraform_workspace_config, {
      dependencies = [
        "infrastructure",
      ]

      providers = [
        "cloudflare",
      ]

      bind_to_account = local.compass_account["execution_role_arn"]

      bind_to_context = merge(local.default_context_binding, {
        name         = "compass"
        merge_record = "records/terraform/infrastructure.json"
      })
    })
  }

  terraform_workspaces = merge(local.database_monitoring_workspaces, local.infrastructure_workspaces)
}

module "infrastructure_pipeline" {
  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/terraform/terraform-pipeline"

  workspaces = local.terraform_workspaces

  workflow = merge(local.terraform_workflow_config, {
    workflow_name = "infrastructure"

    events = {
      push         = true
      pull_request = false
      release      = false
      schedule     = []
      call         = true
      dispatch     = true
    }

    triggers = {
      directories = [
        "config",
        "terraform",
      ]

      branches = [
        "main",
      ]
    }
  })

  save_files = true

  rel_to_root = local.rel_to_root
}
