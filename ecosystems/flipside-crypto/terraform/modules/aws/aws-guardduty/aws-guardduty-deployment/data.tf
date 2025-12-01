data "aws_caller_identity" "delegated_admin" {}

locals {
  delegated_admin_account_id = data.aws_caller_identity.delegated_admin.account_id
}