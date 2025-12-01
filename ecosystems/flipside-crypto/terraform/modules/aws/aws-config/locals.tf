locals {
  aws_config_iam_password_policy = templatefile("${path.module}/config-policies/iam-password-policy.tpl",
    {
      password_require_uppercase = var.password_require_uppercase ? "true" : "false"
      password_require_lowercase = var.password_require_lowercase ? "true" : "false"
      password_require_symbols   = var.password_require_symbols ? "true" : "false"
      password_require_numbers   = var.password_require_numbers ? "true" : "false"
      password_min_length        = var.password_min_length
      password_reuse_prevention  = var.password_reuse_prevention
      password_max_age           = var.password_max_age
    }
  )

  aws_config_acm_certificate_expiration = templatefile("${path.module}/config-policies/acm-certificate-expiration.tpl",
    {
      acm_days_to_expiration = var.acm_days_to_expiration
    }
  )

  aws_config_ami_approved_tag = templatefile("${path.module}/config-policies/ami-approved-tag.tpl",
    {
      ami_required_tag_key_value = var.ami_required_tag_key_value
    }
  )
}