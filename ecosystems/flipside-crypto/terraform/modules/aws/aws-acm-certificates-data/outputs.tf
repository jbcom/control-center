output "certificates" {
  value = local.aws_acm_certificates_data

  description = "AWS ACM certificates for the account"
}