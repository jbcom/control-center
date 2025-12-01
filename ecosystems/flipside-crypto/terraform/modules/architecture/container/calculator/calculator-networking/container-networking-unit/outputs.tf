output "ingress" {
  value = local.ingress

  description = "Ingress for the unit"
}

output "port_mappings" {
  value = local.port_mappings

  description = "Port mappings for the unit"
}
