locals {
  base_asset_docs = {
    for json_key, infrastructure_data in var.infrastructure : json_key => {
      for category_name, category_data in infrastructure_data : category_name => {
        for component_name, component_data in category_data : "${component_name}.md" => templatefile("${path.module}/templates/component.md", {
          component_name = component_name
          component_data = component_data
        })
      }
    }
  }

  asset_docs = merge(flatten([
    for json_key, infrastructure_data in local.base_asset_docs : [
      for category_name, category_data in infrastructure_data : {
        "${var.docs_dir}/${json_key}/${category_name}" = category_data
      } if category_data != {} && (length(var.allowlist) == 0 || contains(var.allowlist, category_name)) && !contains(var.denylist, category_name)
    ]
  ])...)
}

module "module_docs" {
  for_each = var.docs

  source = "../../markdown/markdown-document"

  config = merge(each.value, {
    index = {
      for json_key, infrastructure_data in local.base_asset_docs : json_key => [
        for file_name in sort(keys(infrastructure_data[each.key])) : {
          url   = "./${json_key}/${each.key}/${file_name}"
          title = trimsuffix(file_name, ".md")
        }
      ] if contains(keys(infrastructure_data), each.key)
    }
  })
}

locals {
  module_docs = {
    (var.docs_dir) = {
      for module_name, docs_data in module.module_docs : "${module_name}.md" => docs_data["document"]
    }
  }
}

module "index" {
  source = "../../markdown/markdown-index"

  pattern = "*.md"

  rel_to_root = var.rel_to_root
}

locals {
  readme_base_doc_config = {
    title = coalesce(var.title, module.github_repository_metadata.repository_name)

    description = var.description

    collapsible_index = var.collapsible_index

    index = merge(module.index.index, {
      infrastructure = [
        for file_name in sort(keys(local.module_docs[var.docs_dir])) : {
          url   = "./${file_name}"
          title = trimsuffix(file_name, ".md")
        }
      ]
    })
  }
}

module "readme_doc_config" {
  source = "../../utils/deepmerge"

  source_maps = [
    local.readme_base_doc_config,
    var.extra_readme_configuration,
  ]
}

locals {
  readme_doc_config = module.readme_doc_config.merged_maps
}

module "readme_doc" {
  source = "../../markdown/markdown-document"

  config = local.readme_doc_config
}

module "docs" {
  source = "../../files"

  files = [
    local.asset_docs,
    local.module_docs,
    {
      (var.docs_dir) = {
        "README.md" = module.readme_doc.document
      }
    }
  ]

  rel_to_root = var.rel_to_root
}