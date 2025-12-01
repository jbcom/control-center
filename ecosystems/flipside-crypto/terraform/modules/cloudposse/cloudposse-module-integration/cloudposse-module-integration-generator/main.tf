locals {
  repository_name = var.module_config["repository_name"]
  repository_tag  = var.module_config["repository_tag"]

  module_name = replace(var.module_name, "-", "_")

  raw_module_config = merge(var.module_config, {
    module_name = local.module_name

    parent_module_name = null

    infrastructure_merge_key   = local.module_name
    infrastructure_source_name = local.module_name
    infrastructure_source_key  = null

    module_source  = format("cloudposse/%s/aws", trimprefix(local.repository_name, "terraform-aws-"))
    module_version = format("v%s", local.repository_tag)
  })

  name_generator = local.raw_module_config["name_generator"]

  password_parameter_generators_from_config = {
    for name in local.raw_module_config["map_password_to"] : name => "|PASSWORD|"
  }

  parameter_generators_from_config = merge(local.password_parameter_generators_from_config, {
    (local.raw_module_config["kms_key_id_key"])  = "|KMS_KEY_ID|"
    (local.raw_module_config["kms_key_arn_key"]) = "|KMS_KEY_ARN|"
    (local.raw_module_config["vpc_id_key"])      = "|VPC_ID|"
    (local.raw_module_config["zone_id_key"])     = "|ZONE_ID|"

    (local.raw_module_config["security_group_create_before_destroy_key"]) = "|SECURITY_GROUP_REPLACE_BEFORE_CREATE|"
    }, {
    for k in local.raw_module_config["map_admin_principals_to"] : k => "|ADMIN_PRINCIPALS|"
    }, {
    for k in local.raw_module_config["map_kms_key_arn_to"] : k => "|KMS_KEY_ARN|"
    }, {
    for k in local.raw_module_config["map_artifacts_bucket_arn_to"] : k => "|ARTIFACTS_BUCKET_ARN|"
  })

  required_variable_files = [
    "context.tf",
    "variables.tf",
  ]

  override_module = lookup(var.module_config, "override_module", false)

  module_variable_files = distinct(concat(local.raw_module_config["variable_files"], local.required_variable_files))
}

module "cloudposse-module-variables" {
  source = "../../../terraform/terraform-get-remote-terraform-variables"

  repository_name      = local.override_module ? "FlipsideCrypto/terraform-infrastructure" : "cloudposse/${local.repository_name}"
  repository_tag       = local.override_module ? "main" : local.repository_tag
  variable_files       = local.override_module ? formatlist("modules/infrastructure/infrastructure-resources/infrastructure-resources-overrides/%s/%s", local.repository_name, local.module_variable_files) : local.module_variable_files
  defaults             = yamldecode(file("${path.module}/global/variables.yaml"))
  overrides            = local.raw_module_config["variables"]
  parameter_generators = local.parameter_generators_from_config

  map_name_to = {
    for variable_name in local.raw_module_config["map_name_to"] : variable_name => local.name_generator
  }

  map_sanitized_name_to = {
    for variable_name in local.raw_module_config["map_sanitized_name_to"] : variable_name =>
    "replace(title(replace(replace(${local.name_generator}, \"-\", \" \"), \"_\", \" \")), \" \", \"\")"
  }

  requires_github_authentication = local.override_module



  log_file_name = "${local.module_name}-remote_variables.log"

  verbose = true

  verbosity = 2
}

locals {
  variables_data = module.cloudposse-module-variables.variables
}

module "variables-contain-fields" {
  for_each = local.variables_data

  source = "./cloudposse-module-integration-generator-test"

  variable_name = each.key
  variable_data = each.value
}

locals {
  base_file_name = join("-", compact([
    local.raw_module_config["file_name_prefix"],
    local.raw_module_config["module_name"],
    local.raw_module_config["file_name_suffix"],
  ]))

  base_module_config = merge(local.raw_module_config, {
    variables = local.variables_data

    paths = {
      for path_name, path_data in var.paths : path_name => merge(path_data, {
        base_file_name = local.base_file_name
      })
    }

    generate_password = local.raw_module_config["generate_password"] ? true : (local.password_parameter_generators_from_config != {} ? true : false)

    raw_denylist  = local.raw_module_config["denylist"]
    raw_allowlist = local.raw_module_config["allowlist"]
  })
}

module "config" {
  source = "./cloudposse-module-integration-generator-config"

  module_config = local.base_module_config
}

module "resources" {
  source = "./cloudposse-module-integration-generator-resources"

  module_config = module.config.config
}

locals {
  module_resources_config = module.resources.config

  raw_variable_snippet_data = {
    for variable_name, variable_data in local.module_resources_config["variables"] : variable_name => {
      Default  = try(coalesce(variable_data["override_value"], variable_data["default_generator"], variable_data["default_value"]), null)
      Override = variable_data["parameter_generator"]
      Required = variable_data["required"]
      Type     = variable_data["type"]
    }
  }

  variable_snippet_data = {
    for variable_name, variable_data in local.raw_variable_snippet_data : variable_name => [
      for k, v in variable_data : {
        title   = k
        content = try(tostring(v), format("<ul>\n%s\n</ul>", join("\n", formatlist("<li>%s</li>", tolist(v)))), format("<code>\n%s\n</code>", yamlencode(v)))
      } if v != null
    ]
  }
}

locals {
  descriptors = {
    Default  = "Either a default value or a generator used to produce a default value using Terraform"
    Override = "A value or generator that always overrides any value set"
    Required = "Whether the parameter must be set or not"
    Type     = "The type of the parameter as dictated by Terraform's <a href=\"https://developer.hashicorp.com/terraform/language/expressions/types\">types and values documentation</a>"
  }

  docs_config = {
    title = "Configuration"

    description = <<EOT
${var.module_config.description}

Builds the resources(s) from <a href="https://github.com/cloudposse/${var.module_config.repository_name}">${var.module_config.repository_name}/${var.module_config.repository_tag}</a>

This is done by adding a declaration for the desired asset in <a href="config/infrastructure/${local.module_name}.yaml">../config/infrastructure/${local.module_name}.yaml</a>.

Each parameter may or may not contain any of the following:
%{for name, description in local.descriptors~}

<dl>
<dt>${name}</dt>
<dd>${replace(replace(replace(replace(replace(description, "\n", "\n\n"), ". ", ".\n\n"), "`{", "<code>\n{"), "}`", "}\n</code>"), "e.g.\n\n", "e.g. ")}</dd>
</dl>
%{endfor~}

Use the parameters to construct the specification for your asset.
EOT

    format_headings = false

    sections = [
      for variable_name, variable_data in local.module_resources_config["variables"] : {
        title = variable_name

        description = replace(replace(replace(replace(replace(variable_data["description"], "\n", "\n\n"), ". ", ".\n\n"), "`{", "<code>{"), "}`", "}</code>"), "e.g.\n\n", "e.g. ")

        snippets = local.variable_snippet_data[variable_name]
      }
    ]
  }
}
