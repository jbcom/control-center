module "efs_filesystem_data" {
  for_each = var.task_config["volumes"]

  source = "../../../../../infrastructure/infrastructure-metadata"

  category_name = "efs_filesystems"

  matchers = each.value.matchers

  account_map = lookup(each.value, "accounts", {})

  context = var.context

  log_file_name = "${each.key}-infrastructure-metadata.log"
}

locals {
  raw_efs_filesystem_data = {
    for volume_name, volume_data in module.efs_filesystem_data : volume_name => volume_data["asset"]
  }
}

data "assert_test" "efs_filesystem_has_id_and_arn" {
  for_each = local.raw_efs_filesystem_data

  test = try(lookup(each.value, "arn", "") != "" && lookup(each.value, "id", "") != "", false)

  throw = "EFS filesystem ${each.key} in task ${var.task_name} is missing at least one of ID, ARN:\n\n${yamlencode(module.efs_filesystem_data)}"
}

locals {
  base_efs_filesystem_data = {
    for volume_name, volume_data in local.raw_efs_filesystem_data : volume_name => volume_data
    if lookup(volume_data, "arn", "") != "" && lookup(volume_data, "id", "") != ""
  }

  efs_filesystem_data = flatten([
    for volume_name, volume_data in local.base_efs_filesystem_data : [
      {
        host_path = null
        name      = volume_name

        efs_volume_configuration = [
          {
            file_system_id          = volume_data["id"]
            root_directory          = "/"
            transit_encryption      = "ENABLED"
            transit_encryption_port = null
            authorization_config = [
              {
                access_point_id = null
                iam             = "ENABLED"
              }
            ]
          }
        ]
      }
    ]
  ])

  mount_point_data = flatten([
    for volume_name, volume_data in local.base_efs_filesystem_data : [
      {
        containerPath = var.task_config["volumes"][volume_name].mount_point
        sourceVolume  = volume_name
        readOnly      = false
      }
    ]
  ])

  filesystem_arns = compact([
    for _, volume_data in local.base_efs_filesystem_data : volume_data["arn"]
  ])

  filesystem_policy_identifier_ssm_paths = {
    for volume_name, volume_config in var.task_config["volumes"] : volume_name =>
    lookup(volume_config, "policy_identifier_ssm_paths", [])
  }

  task_filesystems = {
    for volume_name, volume_data in local.base_efs_filesystem_data : volume_data["id"] => merge(volume_data, {
      external_policy_identifier_arns = lookup(local.filesystem_policy_identifier_data, volume_name, [])
    })
  }
}

module "filesystem_policy_identifiers" {
  for_each = local.filesystem_policy_identifier_ssm_paths

  source  = "cloudposse/ssm-parameter-store/aws"
  version = "0.13.0"

  parameter_read = each.value

  context = var.context
}

locals {
  filesystem_policy_identifier_data = {
    for volume_name, parameter_data in module.filesystem_policy_identifiers : volume_name => parameter_data["values"]
  }
}

data "aws_iam_policy_document" "efs_policy_document" {
  count = length(local.filesystem_arns) > 0 ? 1 : 0

  statement {
    actions = [
      "elasticfilesystem:Client*",
    ]

    resources = local.filesystem_arns
  }
}