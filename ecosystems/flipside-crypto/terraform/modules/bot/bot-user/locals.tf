locals {
  username = format("%s-bot", var.username)

  tags = merge(var.context["tags"], {
    Name = local.username
  })

  policies = var.attach_admin_policy ? distinct(flatten(concat(["arn:aws:iam::aws:policy/AdministratorAccess"], var.custom_policy_arns))) : var.custom_policy_arns
}