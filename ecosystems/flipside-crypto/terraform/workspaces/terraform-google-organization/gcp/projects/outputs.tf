output "context" {
  value = merge(local.context, {
    projects = local.projects
  })

  sensitive = true

  description = "Context data"
}