output "environment_overrides" {
  value = local.environment_overrides

  sensitive = true
}

output "monitoring_targets" {
  value = merge(flatten([
    for cluster_name, cluster_params in module.rds : [
      for instance_id, instance_params in cluster_params.cluster_instances : {
        (instance_params.identifier) = cluster_params.cluster_master_password
      }
    ]
  ])...)
}
