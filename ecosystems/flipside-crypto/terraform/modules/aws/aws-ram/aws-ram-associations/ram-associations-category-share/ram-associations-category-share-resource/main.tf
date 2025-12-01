resource "aws_ram_resource_association" "default" {
  for_each = toset(var.resource_share_arns)

  resource_arn       = var.resource_arn
  resource_share_arn = each.value
}