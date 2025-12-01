locals {
  slug_to_name_map = {
    stg  = "Staging"
    prod = "Production"
  }
}

resource "doppler_environment" "default" {
  project = var.doppler_project
  slug    = var.environment_name
  name    = local.slug_to_name_map[var.environment_name]
}

resource "doppler_config" "default" {
  project     = var.doppler_project
  environment = doppler_environment.default.slug
  name        = "${var.environment_name}_copilot"
}

data "aws_iam_policy_document" "doppler_ssm_policy_document" {
  statement {
    sid       = "DopplerSSM"
    effect    = "Allow"
    resources = ["*"]

    actions = [
      "ssm:PutParameter",
      "ssm:LabelParameterVersion",
      "ssm:DeleteParameter",
      "ssm:RemoveTagsFromResource",
      "ssm:GetParameterHistory",
      "ssm:AddTagsToResource",
      "ssm:GetParametersByPath",
      "ssm:GetParameters",
      "ssm:GetParameter",
      "ssm:DeleteParameters"
    ]
  }
}

module "role" {
  source  = "cloudposse/iam-role/aws"
  version = "0.19.0"

  environment = var.environment_name
  attributes  = ["doppler"]

  policy_description = "Allow Doppler integration access to SSM"
  role_description   = "IAM role with permissions to perform actions on SSM resources"

  principals = {
    AWS = ["arn:aws:iam::299900769157:user/doppler-integration-operator"]
  }

  assume_role_conditions = [
    {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = ["6b099ee9d162b413f57a"]
    }
  ]

  policy_documents = [
    data.aws_iam_policy_document.doppler_ssm_policy_document.json,
  ]

  context = var.context
}

resource "doppler_integration_aws_parameter_store" "default" {
  name            = local.slug_to_name_map[var.environment_name]
  assume_role_arn = module.role.arn
}

resource "doppler_secrets_sync_aws_parameter_store" "default" {
  integration = doppler_integration_aws_parameter_store.default.id
  project     = var.doppler_project
  config      = doppler_config.default.name

  region        = "us-east-1"
  path          = "/compass/${var.environment_name}/"
  secure_string = true
  tags          = var.tags

  delete_behavior = "delete_from_target"
}
