locals {
  modules_dir      = coalesce(var.modules_dir, var.config.modules_dir)
  modules_base_dir = "${local.modules_dir}/${var.config.base_dir}"
  modules_suffix   = trimsuffix(var.config.generated_module_name_prefix, "-")

  path_names = [
    "config",
    "resources",
    "metadata",
    "aggregator",
  ]

  raw_paths     = formatlist("%s/%s-%s", local.modules_base_dir, local.modules_suffix, local.path_names)
  raw_path_data = zipmap(local.path_names, local.raw_paths)

  rel_path_depth = {
    for name, path in local.raw_path_data : name => length(split("/", path))
  }

  paths_data = {
    for name, rel_path_depth in local.rel_path_depth : name => {
      path = local.raw_path_data[name]
      rel_to_root = join("/", [
        for i in range(0, rel_path_depth) : ".."
      ])
    }
  }
}

module "cloudposse-module-generator" {
  for_each = var.config.modules

  source = "./cloudposse-module-integration-generator"

  module_name   = each.key
  module_config = each.value

  paths = local.paths_data
}

locals {
  modules_config = {
    for _, module_data in module.cloudposse-module-generator : module_data["config"]["module_name"] => module_data["config"]
  }
}

module "cloudposse-modules-generated-from-generators" {
  source = "./cloudposse-module-integration-generated-from-generators"

  modules_config = local.modules_config
}

locals {
  modules_from_modules_config = module.cloudposse-modules-generated-from-generators.config

  global_variables_data = yamldecode(file("${path.module}/cloudposse-module-integration-generator/global/variables.yaml"))

  combiner_infrastructure_defaults = {
    (format("%s/defaults", local.raw_path_data["config"])) = {
      "infrastructure.json" = jsonencode({
        for module_name, _ in local.modules_config : module_name => {}
      })
    }
  }

  metadata_infrastructure_config = {
    (format("%s/files", local.raw_path_data["metadata"])) = {
      "config.yaml" = yamlencode({
        for module_name, module_config in local.modules_config : module_name => module_config["merge_across_accounts"]
      })
    }
  }

  templates_dir = "${path.module}/templates"

  generated_module_template_files_data = {
    for path_name, path_value in local.raw_path_data : path_value => {
      for name in fileset("${local.templates_dir}/${path_name}", "*.tpl") : trimsuffix(name, ".tpl") => templatefile("${local.templates_dir}/${path_name}/${name}", merge(var.config, {
        generators = local.modules_config

        generated_from_generators = local.modules_from_modules_config

        paths = local.raw_path_data
      }))
    }
  }

  files_dir = "${path.module}/files"

  generated_module_files_data = {
    for path_name, path_value in local.raw_path_data : path_value => {
      for name in fileset("${local.files_dir}/${path_name}", "*.tf") : name => file("${local.files_dir}/${path_name}/${name}")
    }
  }

  files_data = flatten(concat([
    for module_name, generator_data in local.modules_config : generator_data["files"]
    ], [
    for module_name, generator_data in local.modules_from_modules_config : generator_data["files"]
    ], [
    local.combiner_infrastructure_defaults,
    local.metadata_infrastructure_config,
    local.generated_module_template_files_data,
    local.generated_module_files_data,
  ]))

  files_allowlist = [
    for path_name in var.config.allowlist : try(local.paths_data[path_name]["path"], path_name)
  ]

  files_denylist = [
    for path_name in var.config.denylist : try(local.paths_data[path_name]["path"], path_name)
  ]
}

module "files" {
  source = "../../files"

  files = local.files_data

  file_base_path = var.file_base_path

  file_path_trim_prefix = local.modules_base_dir

  allowlist = local.files_allowlist
  denylist  = local.files_denylist

  rel_to_root = var.rel_to_root
}

locals {
  modules_data = {
    for module_name, module_config in merge(local.modules_config, local.modules_from_modules_config) : module_name => {
      for k, v in module_config : k => v if k != "files"
    }
  }

  module_docs = {
    for _, module_data in module.cloudposse-module-generator : module_data["config"]["module_name"] => module_data["docs"]
  }
}
