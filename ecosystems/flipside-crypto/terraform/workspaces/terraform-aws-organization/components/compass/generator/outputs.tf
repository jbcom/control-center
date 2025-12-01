output "context" {
  value = merge(local.context, {
    copilot_account_id       = local.account_id
    copilot_grantees         = local.grantees
    copilot_tags             = local.copilot_tags
    copilot_environment_tags = local.copilot_environment_tags
    compass_kms_key          = module.kms
    compass_assume_role      = module.compass_assume_role
    global_kms_key_arn       = data.aws_kms_key.global.arn
  })

  sensitive = true

  description = "Context data"
}