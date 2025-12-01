output "data" {
  value = {
    for group_name, merge_data in module.data : group_name => merge_data["merged_maps"]
  }

  description = "Environment config"
}
