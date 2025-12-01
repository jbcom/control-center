module "container_metadata" {
  source = "git@github.com:FlipsideCrypto/container-architecture.git//modules/container-metadata"
}

locals {
  efs_filesystem_policy_arns = try(module.container_metadata.metadata[local.environment]["task_deployments"]["filesystems"], {})
}

data "aws_iam_policy_document" "efs-private" {
  for_each = {
    for fs_name, fs_data in module.efs_filesystems-private : fs_name => fs_data if local.efs_filesystems_private_config[fs_name]["efs_filesystem_policy_enabled"]
  }

  dynamic "statement" {
    for_each = try(local.efs_filesystem_policy_arns[each.value["id"]], null) != null ? [0] : []

    content {
      sid = "allowEcs"

      principals {
        identifiers = local.efs_filesystem_policy_arns[each.value["id"]]["policy_arns"]

        type = "AWS"
      }

      resources = [
        each.value["arn"],
      ]

      actions = [
        "elasticfilesystem:Client*",
      ]
    }
  }

  dynamic "statement" {
    for_each = local.datasync_efs_role_arns[each.key] != "" ? [0] : []

    content {
      sid = "allowDatasync"

      principals {
        identifiers = [
          local.datasync_efs_role_arns[each.key],
        ]

        type = "AWS"
      }

      resources = [
        each.value["arn"],
      ]

      actions = [
        "elasticfilesystem:Client*",
      ]
    }
  }

  dynamic "statement" {
    for_each = local.efs_filesystems_private_config[each.key]["efs_cross_account_policy_enabled"] ? [0] : []

    content {
      sid = "allowCrossAccount"

      principals {
        identifiers = ["*"]
        type        = "AWS"
      }

      actions = [
        "elasticfilesystem:Client*",
      ]

      resources = [
        each.value["arn"],
      ]
    }
  }
}

resource "aws_efs_file_system_policy" "efs-private" {
  for_each = data.aws_iam_policy_document.efs-private

  file_system_id = module.efs_filesystems-private[each.key].id

  policy = each.value.json
}