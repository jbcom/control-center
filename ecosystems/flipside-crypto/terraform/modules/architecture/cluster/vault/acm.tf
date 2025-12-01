resource "aws_acm_certificate" "vault" {
  private_key       = tls_private_key.server.private_key_pem
  certificate_body  = local.certificate_data
  certificate_chain = local.ca_certificate_data
}

locals {
  certificate_arn = aws_acm_certificate.vault.arn
}