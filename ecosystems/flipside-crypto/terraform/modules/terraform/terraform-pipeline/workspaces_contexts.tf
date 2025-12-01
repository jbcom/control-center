locals {
  passthrough_context_parameters = [
    "name",
    "tenant",
    "environment",
    "stage",
    "namespace",
    "attributes",
    "tags",
    "label_order",
    "label_key_case",
    "id_length_limit",
    "ordered",
    "passthrough_data_channel",
  ]

  context_passthrough_parameters = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => {
      for k, v in workspace_config["bind_to_context"] : k => v if contains(local.passthrough_context_parameters, k) && v != null
    }
  }

  context_config_object_parameters = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => {
      for k, v in workspace_config["bind_to_context"] : k => v if !contains(local.passthrough_context_parameters, k) && v != null
    }
  }

  context_state_key = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => workspace_config["bind_to_context"]["state_key"]
  }

  context_object_key = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => coalesce(workspace_config["bind_to_context"]["object_key"], local.context_state_key[workspace_name])
  }

  context_base_tf_json = {
    for workspace_name, context_object_parameters in local.context_passthrough_parameters : workspace_name => {
      context = {
        module = {
          context = merge(local.workspaces_template_variables_config[workspace_name]["parent_context"], {
            source = local.workspaces_module_sources[workspace_name]["context_module_source_full"]
            config = local.context_config_object_parameters[workspace_name]
            }, {
            for k, _ in context_object_parameters : k => "$${local.${k}}"
            }, {
            tags = {
              for k, v in merge(lookup(context_object_parameters, "tags", {}), {
                Terraform    = "terraform"
                Owner        = "DevOps"
                Organization = "FlipsideCrypto"
              }) : k => v if k != "Name"
            }
          })
        }

        locals = merge(context_object_parameters, {
          (local.context_object_key[workspace_name]) = "$${module.context.context}"
        })
      }

      no_context = {
        module = {}
        locals = {}
      }
    }
  }

  context_tf_json_key = {
    for workspace_name, workspace_config in local.workspaces_template_variables_config : workspace_name => (workspace_config["bind_to_context"] != {} && !workspace_config["disable_context"]) ? "context" : "no_context"
  }

  context_tf_json = {
    for workspace_name, tf_json in local.context_base_tf_json : workspace_name => tf_json[local.context_tf_json_key[workspace_name]]
  }
}
