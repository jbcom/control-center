output "datasync_location_arn" {
  value = join("", aws_datasync_location_s3.default.*.arn)

  description = "Location ARN"
}

output "datasync_location_id" {
  value = join("", aws_datasync_location_s3.default.*.id)

  description = "Location ID"
}