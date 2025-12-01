output "saml_provider_arn" {
  value = data.external.awscli_program.result.saml_provider_arn

  description = "SAML provider ARN"
}

output "assumed_role" {
  value = module.assumed-role-data

  sensitive = true

  description = "Assumed role data"
}