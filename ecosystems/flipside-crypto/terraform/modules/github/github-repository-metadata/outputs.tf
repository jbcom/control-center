output "repository_name" {
  value = local.repository_name

  description = "Repository name"
}

output "tld" {
  value = local.repository_local_data["tld"]

  description = "Git repository root directory path"
}

output "rel_to_root" {
  value = local.repository_local_data["rel_to_root"]

  description = "Relative path to the Git repository root"
}

output "metadata" {
  value = local.repository_data

  description = "Repository metadata"
}

output "repositories" {
  value = local.repositories_data

  description = "Metadata for all repositories"
}

output "categories" {
  value = local.metadata["github_categories"]

  description = "Github categories"
}

output "organizations" {
  value = local.metadata["github"]["organizations"]

  description = "Github organizations"
}

output "kms" {
  value = merge(local.metadata["kms"], {
    default = local.metadata["default_kms_key"]
  })

  description = "KMS keys"
}