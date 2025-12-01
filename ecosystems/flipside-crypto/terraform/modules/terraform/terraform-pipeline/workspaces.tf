locals {
  default_provider_config = jsondecode(file("${path.module}/defaults/workspace/providers.json"))

  # Load Doppler and Vault configuration from JSON files
  doppler_json_config_raw = jsondecode(file("${path.module}/defaults/workspace/doppler_json_config.json"))
  vault_json_config_raw   = jsondecode(file("${path.module}/defaults/workspace/vault_json_config.json"))

  # Build doppler_config structure for compatibility
  doppler_config = {
    project = {
      name = local.doppler_json_config_raw.project
    }
    config = {
      name = local.doppler_json_config_raw.config
    }
    required_environment_variables = local.doppler_json_config_raw.required_environment_variables
  }

  # Build vault_config structure for compatibility
  vault_config = {
    url                            = local.vault_json_config_raw.address
    namespace                      = local.vault_json_config_raw.namespace
    required_environment_variables = local.vault_json_config_raw.required_environment_variables
  }

  workspace_sops_config = {
    for workspace_name, workspace_config in var.workspaces : workspace_name => merge({
      arn = workspace_config["secrets_kms_key_arn"]
    }, workspace_config["secrets_kms_key"])
    if workspace_config["secrets_kms_key"] != {} || try(coalesce(workspace_config["secrets_kms_key_arn"]), null) != null
  }

  workspaces_raw_config = {
    for workspace_name, workspace_config in var.workspaces : coalesce(workspace_config["workspace_name"], element(split("/", workspace_name), length(split("/", workspace_name)) - 1)) => merge(workspace_config, {
      provider_config = merge(local.default_provider_config, workspace_config["provider_overrides"])

      providers = distinct(concat(workspace_config["providers"], keys(workspace_config["provider_overrides"]), [
        "aws",
        "doppler",
        ], contains(keys(local.workspace_sops_config), workspace_name) ? [
        "sops",
      ] : []))

      workspaces_dir_name = workspace_config["workspaces_in_root_dir"] ? "" : workspace_config["workspace_dir"]
    })
  }

  workspaces_base_config = {
    for workspace_name, workspace_config in local.workspaces_raw_config : workspace_name => merge(workspace_config, {
      workspace_name = workspace_name
      workspaces_dir = join("/", compact(concat([
        workspace_config["root_dir"],
        ], workspace_config["backend_region"] != "us-east-1" ? [
        workspace_config["backend_region"],
        ] : [], [
        workspace_config["workspaces_dir_name"],
      ])))

      job_name = replace(coalesce(workspace_config["job_name"], workspace_name), "/\\W|_|\\s/", "-")

      dependencies = [
        for dependency_name in workspace_config["dependencies"] : replace(dependency_name, "/\\W|_|\\s/", "-")
      ]
    })
  }

  workspaces_regioned_config = {
    for workspace_name, workspace_config in local.workspaces_base_config : workspace_name => merge(workspace_config, {
      job_name = workspace_config["backend_region"] != "us-east-1" ? format("%s-%s", workspace_config["job_name"], workspace_config["backend_region"]) : workspace_config["job_name"]

      dependencies = [
        for dependency_name in workspace_config["dependencies"] :
        (workspace_config["backend_region"] != "us-east-1" ? format("%s-%s", dependency_name, workspace_config["backend_region"]) : dependency_name)
      ]
    })
  }

  workspaces_module_sources = {
    for name, c in local.workspaces_regioned_config : name => merge(c, {
      default_module_source      = lookup(c, "default_module_source", "git@github.com:FlipsideCrypto/terraform-modules.git/"),
      context_module_source      = coalesce(lookup(c, "context_module_source", null), lookup(c, "default_module_source", "git@github.com:FlipsideCrypto/terraform-modules.git/")),
      context_module_path        = lookup(c, "context_module_path", "utils/context"),
      context_module_source_full = "${coalesce(lookup(c, "context_module_source", null), lookup(c, "default_module_source", "git@github.com:FlipsideCrypto/terraform-modules.git/"))}/${lookup(c, "context_module_path", "utils/context")}"
    })
  }

  workspaces_version_raw_config = {
    for workspace_name, workspace_config in local.workspaces_module_sources : workspace_name => merge(workspace_config, {
      terraform_semver_segments = split(".", workspace_config["terraform_version"])
    })
  }

  workspaces_version_base_config = {
    for workspace_name, version_config in local.workspaces_version_raw_config : workspace_name => merge(version_config, {
      terraform_major_version = version_config["terraform_semver_segments"][0]
      terraform_minor_version = length(version_config["terraform_semver_segments"]) > 1 ? version_config["terraform_semver_segments"][1] : "0"
    })
  }

  workspaces_version_config = {
    for workspace_name, version_config in local.workspaces_version_base_config : workspace_name => merge(version_config, {
      terraform_major_minor_version = join(".", [
        version_config["terraform_major_version"],
        version_config["terraform_minor_version"],
      ])
    })
  }

  workspaces_regions_config = {
    for workspace_name, workspace_config in local.workspaces_version_config
    : workspace_name => merge(workspace_config, {
      aws_provider_regions = distinct(concat(workspace_config["aws_provider_regions"], [
        workspace_config["backend_region"],
      ]))
    })
  }

  workspaces_template_variables_base_config = {
    for workspace_name, workspace_config in local.workspaces_regions_config : workspace_name => merge(workspace_config, {
      backend_workspace_name = coalesce(workspace_config["backend_workspace_name"], workspace_name)
      secrets_dir            = workspace_config["vendor_secrets_dir"]
      use_local_secrets      = workspace_config["vendor_secrets_dir"] != ""
      rel_to_root            = "$${REL_TO_ROOT}"
    })
  }

  workspaces_template_variables_config = {
    for workspace_name, workspace_config in local.workspaces_template_variables_base_config : workspace_name => merge(workspace_config, {
      backend_workspace_name = workspace_config["backend_region"] != "us-east-1" ? format("%s-%s", workspace_config["backend_workspace_name"], workspace_config["backend_region"]) : workspace_config["backend_workspace_name"]
    })
  }

  workspaces_config_tf_json = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => jsondecode(templatefile("${path.module}/templates/workspace/config.tf.json", workspace_config))
  }

  # Vendors configuration: inline Doppler data source (no module)
  # Use actual values from doppler_config during generation
  workspace_vendor_inline = {
    for name, w in local.workspaces_template_variables_config : name => {
      data = {
        doppler_secrets = {
          vendors = {
            config  = local.doppler_config.config.name
            project = local.doppler_config.project.name
          }
        }
      }
      locals = {
        # Doppler secrets data source returns a map directly (not JSON-encoded)
        vendors_data = "$${zipmap([for k in keys(data.doppler_secrets.vendors.map) : lower(k)], values(data.doppler_secrets.vendors.map))}"
      }
    }
    if w["use_vendors"]
  }

  workspaces_workspace_dir = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => join("/", [
      workspace_config["workspaces_dir"],
      coalesce(workspace_config["workspace_dir_name"], workspace_config["workspace_name"]),
    ])
  }

  workspaces_workspace_dir_by_job_name = {
    for _, workspace_config in local.workspaces_template_variables_config : workspace_config["job_name"] => join("/", [
      workspace_config["workspaces_dir"],
      coalesce(workspace_config["workspace_dir_name"], workspace_config["workspace_name"]),
    ])
  }

  # Only include context module - vendors handled via inline Doppler data source
  workspaces_modules = {
    for workspace_name, _ in local.workspaces_config_tf_json : workspace_name =>
    local.context_tf_json[workspace_name]["module"]
  }


  workspaces_tf_json = {
    for workspace_name, tf_json in local.workspaces_config_tf_json : workspace_name => merge(
      local.providers_tf_json[workspace_name],
      {
        terraform = merge(tf_json["terraform"], local.providers_tf_json[workspace_name].terraform)
        data = merge(
          tf_json["data"],
          try(local.workspace_vendor_inline[workspace_name]["data"], {})
        )
        locals = merge(
          tf_json["locals"],
          local.context_tf_json[workspace_name]["locals"],
          try(local.workspace_vendor_inline[workspace_name]["locals"], {}),
          {
            use_local_secrets     = local.workspaces_template_variables_config[workspace_name]["vendor_secrets_dir"] != ""
            secrets_kms_key_arn   = local.workspaces_template_variables_config[workspace_name]["secrets_kms_key_arn"]
            root_dir              = local.workspaces_template_variables_config[workspace_name]["root_dir"]
            workspaces_dir        = local.workspaces_template_variables_config[workspace_name]["workspaces_dir"]
            workspaces_dir_name   = local.workspaces_template_variables_config[workspace_name]["workspaces_dir_name"]
            workspace_dir         = local.workspaces_workspace_dir[workspace_name]
            workspace_secrets_dir = local.workspaces_template_variables_config[workspace_name]["workspace_secrets_dir"]
            vendor_secrets_dir    = local.workspaces_template_variables_config[workspace_name]["vendor_secrets_dir"]
          },
          local.workspaces_local_config_files_config[workspace_name]
        )
      },
      # Only include the module section if there are modules to include
      length(local.workspaces_modules[workspace_name]) > 0 ? { module = local.workspaces_modules[workspace_name] } : {}
    )
  }

  workspaces_docs_data = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => concat(workspace_config["docs_sections_pre"], length(workspace_config["dependencies"]) > 0 ? [
      {
        title       = "Terraform Workspace Dependencies"
        description = <<EOT
This Terraform workspace has dependencies that need to be run ahead of it.
This is configured automatically in the Terraform workflow for this workspace but will need to be accounted for if running manually.

They are:
%{for dependency in workspace_config["dependencies"]~}
* ${dependency}
%{endfor~}
EOT
      }
    ] : [], workspace_config["docs_sections_post"])
  }
}

#
#data "assert_test" "workspace_config_dependencies_all_exist" {
#  for_each = merge(flatten([
#  for workspace_name, workspace_config in local.workspaces_template_variables_config : [
#  for dependency in workspace_config["dependencies"] : {
#    "${workspace_name}//${dependency}" = try(local.workspaces_workspace_dir_by_job_name[dependency], null)
#  }
#  ]
#  ])...)
#
#  test  = each.value != null
#  throw = "${each.key} does not exist:\n${yamlencode(local.workspaces_workspace_dir_by_job_name)}"
#}

locals {
  workspaces_extra_config_files_config = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => merge({
      for file_stem, json_config in workspace_config["extra_json_config"] : "${file_stem}.json" =>
      jsonencode(json_config)
      }, {
      for file_stem, yaml_config in workspace_config["extra_yaml_config"] : "${file_stem}.yaml" =>
      yamlencode(yaml_config)
    })
  }

  workspaces_extra_config_files_dirs = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => join("/", [
      local.workspaces_workspace_dir[workspace_name], workspace_config["config_files_dir"],
    ])
  }

  workspaces_extra_config_files_data = [
    for workspace_name, config_files in local.workspaces_extra_config_files_config : [
      {
        (local.workspaces_extra_config_files_dirs[workspace_name]) = config_files
      }
    ]
  ]

  workspaces_local_config_files_raw_config = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => {
      local_files = workspace_config["local_files"]
      local_json_files = merge(workspace_config["local_json_files"], {
        for file_stem, file_config in workspace_config["extra_json_config"] : file_stem => "$${path.module}/files/${file_stem}.json"
      })

      local_yaml_files = merge(workspace_config["local_yaml_files"], {
        for file_stem, file_config in workspace_config["extra_yaml_config"] : file_stem => "$${path.module}/files/${file_stem}.yaml"
      })
    }
  }

  workspaces_local_config_files_config = {
    for workspace_name, files_config in local.workspaces_local_config_files_raw_config : workspace_name => merge({
      for k, v in files_config["local_files"] : k =>
      format("$${file(\"%s\")}", v)
      }, {
      for k, v in files_config["local_json_files"] : k =>
      format("$${try(jsondecode(file(\"%s\")), {})}", v)
      }, {
      for k, v in files_config["local_yaml_files"] : k =>
      format("$${yamldecode(file(\"%s\"))}", v)
    })
  }

  workspaces_files_base_data = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => merge(concat([{
      "terragrunt.hcl" = templatefile("${path.module}/templates/workspace/terragrunt.hcl", merge(workspace_config, {
        dependencies = {
          for dependency in workspace_config["dependencies"] : dependency => local.workspaces_workspace_dir_by_job_name[dependency]
        }
      }))

      ".terragrunt.tf" = <<-EOT
# Ensures Terragrunt commands will run in this directory
EOT

      ".gitignore" = templatefile("${path.module}/templates/workspace/terraform.gitignore", workspace_config)
      }
      ], [
      {
        for file_name, file_contents in workspace_config["extra_files"] : file_name => replace(file_contents, "$${MODULES_SOURCE}", local.workspaces_module_sources[workspace_name]["default_module_source"]) if file_contents != ""
      }
      ], workspace_config["disable_config"] ? [{}] : [
      {
        "config.tf.json" = jsonencode(local.workspaces_tf_json[workspace_name])
      }
    ])...) if workspace_config["managed"]
  }

  workspace_readme_docs = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => local.workspaces_docs_data[workspace_name]
  }
}

module "readme_doc" {
  for_each = try(nonsensitive(local.workspace_readme_docs), local.workspace_readme_docs)

  source = "../../markdown/markdown-document"

  config = {
    title = "Terraform ${each.key} Workspace"

    sections = each.value
  }
}

module "kms_sops_directory" {
  for_each = try(nonsensitive(local.workspace_sops_config), local.workspace_sops_config)

  source = "../../secrets/kms-sops-directory"

  kms_key_arn = join(",", compact([
    each.value["arn"],
    try(coalesce(each.value["role"]), ""),
  ]))

  base_dir    = local.workspaces_workspace_dir[each.key]
  secrets_dir = local.workspaces_template_variables_config[each.key]["workspace_secrets_dir"]

  docs_dir = local.workspaces_template_variables_config[each.key]["docs_dir"]
}

locals {
  workspaces_docs_dirs = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => join("/", [
      local.workspaces_workspace_dir[workspace_name], workspace_config["docs_dir"],
    ])
  }

  workspaces_docs_files_data = [
    for workspace_name, workspace_config in local.workspaces_template_variables_config : concat([
      {
        (local.workspaces_docs_dirs[workspace_name]) = {
          (workspace_config["readme_name"]) = module.readme_doc[workspace_name].document
        }
      }
      ], contains(keys(module.kms_sops_directory), workspace_name) ? [
      module.kms_sops_directory[workspace_name].files,
    ] : []) if workspace_config["managed"]
  ]

  workspaces_files_data = flatten(concat([
    for workspace_name, files_data in local.workspaces_files_base_data : {
      (local.workspaces_workspace_dir[workspace_name]) = files_data
    }
  ], local.workspaces_docs_files_data, local.workspaces_extra_config_files_data))
}
