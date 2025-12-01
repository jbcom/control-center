module "external-ci-bot-user" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-bot-user"

  username                 = "external-ci"
  attach_admin_policy      = true
  attach_key_pair          = true
  save_secrets_to_github   = true
  generate_gpg_key         = true
  write_key_pair_to_github = true
  create_login_profile     = true

  context = local.context
}

data "aws_iam_policy_document" "requester_pays_bucket_reader" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "requester_pays_bucket_reader" {
  name = "requester-pays-bucket-reader"

  policy = data.aws_iam_policy_document.requester_pays_bucket_reader.json

  tags = merge(local.context["tags"], {
    Name = "requester-pays-bucket-reader"
  })
}

module "requester_pays_bucket_reader" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-bot-user"

  username = "requester-pays-bucket-reader"

  custom_policy_arns = [
    aws_iam_policy.requester_pays_bucket_reader.arn,
  ]

  number_of_policies = 1

  context = local.context
}

module "grafana_cloudwatch_access_policy" {
  source  = "cloudposse/iam-policy/aws"
  version = "2.0.1"

  name = "grafana-cloudwatch"

  iam_policy_enabled = true

  iam_source_policy_documents = [
    for policy_file in fileset("${path.module}/files/policies/grafana-cloudwatch", "*.json") :
    file("${path.module}/files/policies/grafana-cloudwatch/${policy_file}")
  ]

  context = local.context
}

module "grafana_cloudwatch_bot_user" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//aws/aws-bot-user"

  username = "grafana-cloudwatch"

  custom_policy_arns = [
    module.grafana_cloudwatch_access_policy.policy_arn,
  ]

  number_of_policies = 1

  context = local.context
}

locals {
  bots = {
    external_ci        = module.external-ci-bot-user
    grafana_cloudwatch = module.grafana_cloudwatch_bot_user
  }

  admin_bot_users = [
    module.external-ci-bot-user.user_arn,
    local.context["github"]["arn"],
  ]
}

locals {
  records_config = merge({
    bots = {
      for bot_name, bot_data in local.bots : bot_name => {
        for k, v in bot_data : k => v if k != "credentials"
      }
    }
    admin_bot_users = local.admin_bot_users
  })
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspace_dir}"

  log_file_name = "permanent_record.log"
}
