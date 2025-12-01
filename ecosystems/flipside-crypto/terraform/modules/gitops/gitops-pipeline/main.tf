locals {
  repositories_config = var.context["repositories"]
}

module "generator_pipeline" {
  for_each = {
    for repository_name, repository_data in local.repositories_config : repository_name => repository_data["terraform"]["generator"] if repository_data["terraform"]["enabled"]
  }

  source = "../../terraform/terraform-pipeline"

  workspaces = each.value["workspaces"]

  workflow = each.value["workflow"]
}

module "generator_pipeline_files" {
  for_each = module.generator_pipeline

  source = "../../files"

  files = each.value["files"]

  rel_to_root = var.rel_to_root
}