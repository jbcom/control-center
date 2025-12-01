data "aws_iam_roles" "roles" {
  for_each = toset(var.allowlist)

  name_regex  = "AWSReservedSSO_${each.key}_.*"
  path_prefix = "/aws-reserved/sso.amazonaws.com/"
}

locals {
  roles = merge([
    for _, role_data in data.aws_iam_roles.roles : zipmap(tolist(role_data["names"]), tolist(role_data["arns"]))
  ]...)
}