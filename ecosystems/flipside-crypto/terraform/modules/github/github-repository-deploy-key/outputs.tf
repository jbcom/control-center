output "private_key_pem" {
  value = join("", aws_ssm_parameter.param-private_key_pem.*.name)

  description = "SSH private key PEM SSM path"
}

output "public_key_pem" {
  value = join("", aws_ssm_parameter.param-public_key_pem.*.name)

  description = "SSH public key PEM SSM path"
}

output "public_key_openssh" {
  value = join("", aws_ssm_parameter.param-public_key_openssh.*.name)

  description = "SSH public key OpenSSH SSM path"
}