data "aws_iam_policy_document" "vault_server_policy" {
  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]

    resources = [
      local.s3_bucket_arn,
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${local.s3_bucket_arn}/*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "dynamodb:*",
    ]

    resources = [
      local.dynamodb_table_arn,
      "${local.dynamodb_table_arn}/*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ssm:UpdateInstanceInformation",
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel"
    ]

    resources = [
      "*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ec2:DescribeInstances",
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:DescribeKey",
    ]

    resources = [
      local.kms_key_arn,
    ]
  }
}

module "vault_server_role" {
  source  = "cloudposse/eks-iam-role/aws"
  version = "2.2.1"

  name = "vault-server"

  id_length_limit = 64

  eks_cluster_oidc_issuer_url = var.context["eks_cluster_identity_oidc_issuer"]

  service_account_name      = "vault-server"
  service_account_namespace = local.namespace

  aws_iam_policy_document = [
    data.aws_iam_policy_document.vault_server_policy.json,
  ]

  context = var.context
}

resource "kubernetes_service_account_v1" "vault_server" {
  metadata {
    name      = module.vault_server_role.service_account_name
    namespace = local.namespace

    annotations = {
      "eks.amazonaws.com/role-arn" : module.vault_server_role.service_account_role_arn
    }
  }
}

locals {
  service_account_name = kubernetes_service_account_v1.vault_server.metadata[0].name
}