output "datasync_location_arns" {
  value = {
    for mount_target_id, location_data in aws_datasync_location_efs.default : mount_target_id => location_data["arn"]
  }

  description = "Location ARNs"
}

output "datasync_location_ids" {
  value = {
    for mount_target_id, location_data in aws_datasync_location_efs.default : mount_target_id => location_data["id"]
  }

  description = "Location IDs"
}