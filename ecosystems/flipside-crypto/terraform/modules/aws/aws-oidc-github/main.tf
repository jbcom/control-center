locals {
  tags = merge(var.context["tags"], {
    Name = "github"
  })
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test = "StringLike"
      values = [
        "repo:FlipsideCrypto/*:*",
      ]
      variable = "token.actions.githubusercontent.com:sub"
    }

    condition {
      test     = "StringEquals"
      values   = ["sts.amazonaws.com"]
      variable = "token.actions.githubusercontent.com:aud"
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.github.arn]
      type        = "Federated"
    }
  }

  version = "2012-10-17"
}

resource "aws_iam_role" "github" {
  name_prefix = "github-"

  description = "Role assumed by the GitHub OIDC provider"

  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  path = "/"

  max_session_duration = 3600

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "admin" {
  policy_arn = "arn:${local.partition}:iam::aws:policy/AdministratorAccess"
  role       = aws_iam_role.github.id
}

resource "aws_iam_openid_connect_provider" "github" {
  client_id_list = [
    "https://github.com/FlipsideCrypto",
    "sts.amazonaws.com",
  ]

  url = "https://token.actions.githubusercontent.com"

  thumbprint_list = [
    data.tls_certificate.github.certificates[0].sha1_fingerprint,
  ]

  tags = local.tags
}