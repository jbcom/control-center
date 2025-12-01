output "total_cpu" {
  value = local.nearest_supported_cpu_value

  description = "Calculated nearest supported CPU value to use for the total"
}

output "total_memory" {
  value = local.nearest_supported_memory_value

  description = "Calculated nearest supported memory value to use for the total"
}

output "unit_cpu" {
  value = local.total_usable_cpu / var.scale

  description = "Calculated unit CPU"
}

output "unit_memory" {
  value = local.total_usable_memory / var.scale

  description = "Calculated unit memory"
}
