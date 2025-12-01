locals {
  enabled   = var.config["datasync"]
  encrypted = var.config["encrypted"]

  access_points = try(zipmap(var.data["access_point_ids"], var.data["access_point_arns"]), {})

  name = "datasync-location-efs-${var.data["id"]}"
  arn  = var.data["arn"]

  tags = merge(var.context["tags"], {
    Name = local.name
  })
}

data "aws_efs_mount_target" "default" {
  for_each = local.enabled ? toset(var.data["mount_target_ids"]) : []

  mount_target_id = each.key
}

data "aws_subnet" "default" {
  for_each = data.aws_efs_mount_target.default

  id = each.value.subnet_id
}

resource "aws_datasync_location_efs" "default" {
  for_each = data.aws_efs_mount_target.default

  efs_file_system_arn = each.value.file_system_arn

  access_point_arn = try(local.access_points[var.config["datasync_access_point_id"]], null)

  in_transit_encryption = local.encrypted ? "TLS1_2" : "NONE"

  file_system_access_role_arn = local.encrypted ? var.role_arn : null

  ec2_config {
    security_group_arns = [
      var.data["security_group_arn"],
    ]

    subnet_arn = data.aws_subnet.default[each.key].arn
  }

  tags = merge(local.tags, {
    Name = "${local.name}-${each.key}"
  })
}