output "context" {
  description = "Context data"
  value = merge(local.context, {
    gws = merge(local.context.gws, {
      org_units = local.flattened_org_units
      users     = local.gws_users
      groups    = local.gws_groups
    })
    gcp = merge(local.context.gcp, {
      active_projects = local.gcp_active_projects
    })
  })

  sensitive = true
}
