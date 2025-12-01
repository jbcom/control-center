# PGP Secret Decrypter Module
# This module decrypts PGP-encrypted secrets using Keybase

# External data source to decrypt the secret
data "external" "decrypt_secret" {
  program = ["bash", "${path.module}/bin/decrypt_secret.sh"]

  query = {
    encrypted_secret = var.encrypted_secret
  }
}

# Output the decrypted secret
output "decrypted_secret" {
  description = "The decrypted secret"
  value       = data.external.decrypt_secret.result.secret
  sensitive   = true
}
