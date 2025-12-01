output "sops_yaml" {
  value = local.sops_yaml

  description = "Generated SOPS YAML config"
}

output "files" {
  value = local.files

  description = "Files data"
}