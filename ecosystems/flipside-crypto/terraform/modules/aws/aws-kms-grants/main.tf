locals {
  grantee_principals = distinct(compact(concat(var.grantee_principals, [
    var.grantee_principal,
  ])))
}

module "this" {
  for_each = toset(local.grantee_principals)

  source = "./aws-kms-grant"

  kms_key_arn  = var.kms_key_arn
  kms_key_arns = var.kms_key_arns

  grantee_principal = each.key
}