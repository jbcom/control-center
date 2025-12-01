# Variables for the PGP Secret Decrypter module

variable "encrypted_secret" {
  description = "The PGP-encrypted secret to decrypt (base64 encoded)"
  type        = string
  sensitive   = true
}
