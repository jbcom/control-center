output "secrets" {
  value = [
    for secret_key, secret_data in local.ecs_secret_data : {
      name      = secret_key
      valueFrom = secret_data["arn"]
    }
  ]

  description = "Map of secret keys to corresponding ARNs"
}

output "map_secrets" {
  value = {
    for secret_key, secret_data in local.ecs_secret_data : secret_key => secret_data["arn"]
  }

  description = "Map of secret keys to corresponding ARNs"
}

output "map_secret_names" {
  value = {
    for secret_key, secret_data in local.ecs_secret_data : secret_key => secret_data["name"]
  }

  description = "Map of secret keys to names"
}

output "policy_documents" {
  value = local.ecs_secret_data != {} ? [
    data.aws_iam_policy_document.secrets_retrieval_policy_document.json,
  ] : []

  description = "Policy documents for retrieving the secret(s)"
}

output "policy_arn" {
  value = join("", aws_iam_policy.default[*].arn)

  description = "Policy ARN"
}
