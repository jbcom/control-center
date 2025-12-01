output "modules" {
  value = local.modules_data

  description = "CloudPosse generated modules and their children, if any"
}

output "docs" {
  value = local.module_docs

  description = "CloudPosse module documentation"
}

output "allowlist" {
  value = local.files_allowlist

  description = "Files allowlist"
}

output "denylist" {
  value = local.files_denylist

  description = "Files denylist"
}