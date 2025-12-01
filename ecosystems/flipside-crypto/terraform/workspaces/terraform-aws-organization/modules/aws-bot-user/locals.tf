locals {
  username = format("%s-bot", var.username)

  tags = merge(var.context["tags"], {
    Name = local.username
  })
}