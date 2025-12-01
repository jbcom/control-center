output "user_name" {
  value = aws_iam_user.this.name

  description = "Bot username"
}

output "user_arn" {
  value = aws_iam_user.this.arn

  description = "Bot user ARN"
}

output "credentials" {
  value = {
    access_key        = aws_iam_access_key.this.id
    secret_access_key = aws_iam_access_key.this.secret
  }

  sensitive = true

  description = "Credentials"
}

output "keybase_password_decrypt_command" {
  description = "Decrypt user password command"
  value       = try("echo \"${aws_iam_user_login_profile.this[0].encrypted_password}\" | base64 --decode | keybase pgp decrypt", "")
}

output "keybase_password_pgp_message" {
  description = "Encrypted password"
  value = try(<<EOF
-----BEGIN PGP MESSAGE-----
Version: Keybase OpenPGP v2.0.76
Comment: https://keybase.io/crypto
${aws_iam_user_login_profile.this[0].encrypted_password}
-----END PGP MESSAGE-----
EOF
  , "")

}

output "parameters" {
  value = {
    for parameter_name in module.parameter-store.names : trimprefix(parameter_name, "/bots/${local.username}/") => parameter_name
  }

  description = "Parameters"
}

output "eks_user" {
  value = [
    {
      userarn  = aws_iam_user.this.arn
      username = aws_iam_user.this.name
      groups = [
      "system:masters"]
  }]

  description = "EKS user assignment for cluster authentication"
}

output "docs" {
  value = {
    order = [
      "name",
      "arn",
      "parameters",
    ]

    columns = {
      name = [aws_iam_user.this.name]
      arn  = [aws_iam_user.this.arn]
      parameters = [
        <<EOT
<ul>
%{for parameter in keys(module.parameter-store.arn_map)~}
<li>${parameter}</li>
%{endfor~}
</ul>
EOT
      ]
    }
  }

  sensitive = true

  description = "Documentation sections"
}
