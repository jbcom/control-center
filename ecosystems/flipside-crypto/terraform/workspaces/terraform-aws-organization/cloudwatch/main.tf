resource "aws_cloudformation_stack" "account_list_sharing" {
  name         = "CloudWatch-CrossAccount-ListAccounts"
  template_url = "https://cloudwatch-console-static-content-prod-iad.s3.us-east-1.amazonaws.com/fddd0b0fc015a2fcf843feebe4c1461114ab7c9d/cross-account/CloudWatch-CrossAccountListAccountsRole-AccountList-aws.yaml"
  capabilities = ["CAPABILITY_NAMED_IAM"]

  parameters = {
    MonitoringAccountIds = local.account_id
  }
}

resource "aws_cloudformation_stack_set" "oam_configuration" {
  name          = "CrossAccount-OAM-Setup"
  template_body = file("${path.module}/files/oam.yaml")
  capabilities  = ["CAPABILITY_NAMED_IAM"]

  permission_model        = "SELF_MANAGED"
  execution_role_name     = "AWSControlTowerExecution"
  administration_role_arn = "arn:aws:iam::${local.account_id}:role/service-role/AWSControlTowerStackSetRole"
}

locals {
  accounts = merge(local.context["networked_accounts"], local.context["system_accounts"], local.context["isolated_accounts"])
}

resource "aws_cloudformation_stack_set_instance" "oam_configuration" {
  for_each = {
    for k, v in local.accounts : k => v
    if k != local.account_id
  }

  stack_set_name = aws_cloudformation_stack_set.oam_configuration.name
  account_id     = each.value.account_id
  region         = local.region
}

locals {
  records_config = {
    account_list_role = {
      stack_id = aws_cloudformation_stack.account_list_sharing.id
      role_arn = "arn:aws:iam::${local.account_id}:role/CloudWatch-CrossAccountSharing-ListAccountsRole"
    }
  }
}

module "permanent_record" {
  source = "git@github.com:FlipsideCrypto/terraform-modules.git//utils/permanent-record"

  records = local.records_config

  records_dir = "records/${local.workspaces_dir}"
}
