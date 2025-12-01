output "records" {
  value = {
    authorized_execution_role_arns = local.authorized_execution_role_arns

    secret_policy = jsondecode(local.secret_policy_json)

    #    mongodb_atlas = merge(local.mongodb_atlas_config, {
    #      regions = local.mongodb_atlas_regions
    #    })
  }

  sensitive = true

  description = "Records data"
}

output "pipeline" {
  value = module.pipeline

  description = "Pipeline data"
}