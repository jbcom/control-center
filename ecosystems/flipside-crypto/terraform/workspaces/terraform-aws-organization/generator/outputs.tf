output "context" {
  value = merge({
    for k, v in local.context : k => v if !contains(["guards", "units", "control_tower", "organization", "permission_sets", "policies"], k)
  })

  sensitive   = true
  description = "Context data with no organization, control tower, or permission sets data. This will be passed separately to the organization workspace."
}
