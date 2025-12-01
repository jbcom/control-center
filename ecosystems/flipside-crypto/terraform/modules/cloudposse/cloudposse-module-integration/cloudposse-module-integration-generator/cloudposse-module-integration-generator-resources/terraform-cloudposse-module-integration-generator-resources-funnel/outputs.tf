output "parameters" {
  value = local.module_parameters_data

  description = "Module parameters"
}

output "denylist" {
  value = local.denylist_data

  description = "Denylist"
}