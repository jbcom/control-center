resource "aws_iam_service_linked_role" "this" {
  for_each = setsubtract(local.service_linked_roles, var.service_linked_roles_denylist)

  aws_service_name = each.value

  tags = var.tags
}