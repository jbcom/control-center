locals {
  sops_yaml = yamlencode({
    creation_rules = [
      {
        path_regex = "${var.secrets_dir}/.*"

        kms = var.kms_key_arn
      }
    ]
  })

  files = var.enabled ? [
    {
      (var.base_dir) = {
        ".sops.yaml" = local.sops_yaml
      }

      "${var.base_dir}/${var.docs_dir}" = {
        (coalesce(var.readme_name, "${basename(var.secrets_dir)}.md")) = templatefile("${path.module}/templates/README.md", {
          secrets_dir = var.secrets_dir
          kms_key_arn = var.kms_key_arn
        })
      }

      "${var.base_dir}/${var.secrets_dir}" = {
        "README.md" = <<EOT
# Secrets Directory

## Warning

All files (other than this README) **must** be encrypted with SOPS before committing to the Git history.

It is your responsibility as a code maintainer to ensure that this takes place.
EOT
      }
    }
  ] : []
}

module "files" {
  count = var.save_files ? 1 : 0

  source = "../../files"

  files = local.files

  rel_to_root = var.rel_to_root
}