resource "tls_private_key" "server" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_cert_request" "server" {
  private_key_pem = tls_private_key.server.private_key_pem

  subject {
    common_name = local.shared_san
  }

  dns_names = [
    local.shared_san,
    "localhost",
  ]

  ip_addresses = [
    "127.0.0.1",
  ]
}

resource "kubernetes_secret_v1" "tls" {
  metadata {
    name      = "vault-server-tls"
    namespace = local.namespace
  }

  binary_data = {
    "vault.key" = base64encode(tls_private_key.server.private_key_pem)
    "vault.crt" = base64encode(trimspace(
      <<EOF
${local.certificate_data}
${local.ca_certificate_data}
EOF
    ))
  }
}

locals {
  tls_secret = kubernetes_secret_v1.tls.metadata[0].name
}