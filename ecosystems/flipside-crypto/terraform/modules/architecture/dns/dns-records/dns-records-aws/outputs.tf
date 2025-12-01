output "zones" {
  value = {
    for zone_name, zone_data in module.default : zone_name => zone_data["zone_id"]
  }

  description = "Zone IDs"
}