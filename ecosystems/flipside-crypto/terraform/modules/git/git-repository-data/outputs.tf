output "name" {
  value = local.result_data["name"]

  description = "Git repository name"
}

output "tld" {
  value = local.result_data["tld"]

  description = "Git repository root directory path"
}

output "rel_to_root" {
  value = local.result_data["rel_to_root"]

  description = "Relative path to the Git repository root"
}
