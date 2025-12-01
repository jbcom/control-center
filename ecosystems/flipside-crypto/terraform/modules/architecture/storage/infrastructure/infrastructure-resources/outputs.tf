output "context" {
  value = merge(var.context, {
    infrastructure = local.provisioned_infrastructure_data
    secret_policy  = local.secret_policy_json
  })

  description = "Context data"
}
