data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole", ]
    principals {
      identifiers = ["datasync.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "default" {
  count = var.enabled ? 1 : 0

  name = var.role_name

  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = merge(var.tags, {
    Name = var.role_name
  })
}