locals {
  kms_config = var.config["kms"]

  file_base_path = lookup(var.config, "file_base_path", "repository-files/${var.repository_name}")

  terraform_generator_config = try(var.config["terraform"]["generator"], {})

  use_sync = var.config.use_sync

  repository_config = var.config["repository"]
}

module "repository_secrets" {
  source = "../../secrets/kms-sops-directory"

  kms_key_arn = local.kms_config["generated_kms_key_arn"]

  enabled = local.kms_config["enabled"]

  base_dir    = "."
  secrets_dir = lookup(local.kms_config, "secrets_dir", "secrets")
  docs_dir    = lookup(local.kms_config, "docs_dir", "docs")
}

module "generator_pipeline" {
  count = try(var.config["terraform"]["enabled"], false) && try(local.terraform_generator_config["enabled"], true) ? 1 : 0

  source = "../../terraform/terraform-pipeline"

  workspaces = {
    generator = merge(local.terraform_generator_config["workspace"], (try(var.config["terraform"]["pipeline_config"], true) ? [
      {
        extra_json_config = merge(try(local.terraform_generator_config["workspace"]["extra_json_config"], {}), {
          pipeline_config = var.config
        })

        extra_files = merge(try(local.terraform_generator_config["workspace"]["extra_files"], {}), {
          "pipeline.tf.json" = jsonencode({
            locals = {
              pipeline_name = var.repository_name

              terraform_config = "$${local.pipeline_config.terraform}"

              terraform_workspace_config = "$${local.terraform_config.workspace}"
              terraform_workflow_config  = "$${local.terraform_config.workflow}"

              default_root_dir         = "$${local.terraform_workspace_config.root_dir}"
              default_workspace_dir    = "$${local.terraform_workspace_config.workspace_dir}"
              nested_root_dir          = "$${local.default_root_dir}/$${local.default_workspace_dir}"
              nested_root_dir_template = "$${local.nested_root_dir}/%s"

              default_context_binding = "$${local.terraform_workspace_config.bind_to_context}"

              backend_path_template               = "$${local.terraform_workspace_config.backend_bucket_workspaces_path}/%s/terraform.tfstate"
              nested_backend_path_prefix_template = "$${local.terraform_workspace_config.backend_bucket_workspaces_path}/%s"
              nested_backend_path_template        = "$${local.nested_backend_path_prefix_template}/%s/terraform.tfstate"
            }
          })
        })
      }
    ] : [])...)
  }

  workflow = local.terraform_generator_config["workflow"]
}

module "files" {
  source = "../../files"

  files = flatten(concat(module.repository_secrets.files, module.generator_pipeline.*.files))

  file_base_path = local.file_base_path

  rel_to_root = var.rel_to_root

  write_files = local.use_sync
}

resource "github_repository_file" "direct" {
  for_each = {
    for file_path, file_data in module.files.files : trimprefix(file_path, "./${var.rel_to_root}/${local.file_base_path}/") => file_data if !local.use_sync
  }

  repository          = local.repository_config.name
  branch              = local.repository_config.default_branch
  file                = each.key
  content             = each.value
  commit_message      = "Managed by Terraform [skip actions]"
  commit_author       = "Internal Tooling"
  commit_email        = "internal-tooling-bot@flipsidecrypto.com"
  overwrite_on_create = true
}

locals {
  sync_targets = local.use_sync ? concat([
    for file_path, _ in module.files.raw : {
      source = "${local.file_base_path}/${file_path}"
      dest   = file_path
    }
    ], lookup(var.config, "bootstrap_github_actions", false) ? [
    {
      source = ".github/release.yml"
      dest   = "./.github/release.yml"
    },
    {
      source = ".github/renovate.json"
      dest   = "./.github/renovate.json"
    },
  ] : []) : []
}
