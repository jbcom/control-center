output "cluster" {
  value = merge(var.cluster_config, {
    cluster_id        = aws_ecs_cluster.default.id
    cluster_name      = aws_ecs_cluster.default.name
    cluster_arn       = aws_ecs_cluster.default.arn
    autoscaling_group = module.autoscaling_group
    security_group_id = local.cluster_security_group_id
    instance_role     = module.cluster_instance_role
    log_group         = aws_cloudwatch_log_group.default.name
    cluster_secrets = merge(module.cluster_secrets, {
      policy = module.cluster_secrets_policy
    })

    containers = {
      for container_name, container_data in var.cluster_config.containers : container_name => merge(container_data, {
        definitions = concat([
          module.container_definition_datadog_agent.json_map_object,
          module.container_definition_log_router.json_map_object,
          ], [
          for _, container_definition in module.container_definition : container_definition["json_map_object"]
        ])

        secrets = module.cluster_secrets.secrets

        efs_volumes = [
          for container_path, volume_data in module.efs : {
            host_path = null
            name      = replace(container_path, "/", "-")

            efs_volume_configuration = [
              {
                file_system_id          = volume_data["id"]
                root_directory          = "/"
                transit_encryption      = "DISABLED"
                transit_encryption_port = null
                authorization_config    = []
              }
            ]
          }
        ]
      })
    }

    volumes = module.efs
  })

  description = "Cluster data"
}
