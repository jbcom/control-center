output "aws_group_id" {
  value = aws_identitystore_group.this.group_id

  description = "ID for the AWS group"
}

output "aws_group_external_ids" {
  value = aws_identitystore_group.this.external_ids

  description = "External IDs for the AWS group"
}
