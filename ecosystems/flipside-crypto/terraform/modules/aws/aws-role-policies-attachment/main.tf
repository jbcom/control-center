resource "aws_iam_role_policy_attachment" "this" {
  for_each = toset(var.policy_arns)

  policy_arn = each.key
  role       = var.role_name
}