locals {
  kms_key_arns = distinct(compact(concat(var.kms_key_arns, [
    var.kms_key_arn,
  ])))
}

resource "aws_kms_grant" "this" {
  for_each = toset(local.kms_key_arns)

  key_id            = each.key
  grantee_principal = var.grantee_principal
  operations        = var.operations
}