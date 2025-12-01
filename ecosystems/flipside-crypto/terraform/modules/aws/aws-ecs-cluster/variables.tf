variable "cluster_name" {
  type = string

  description = "Cluster name"
}

variable "cluster_config" {
  type = object({
    name          = string
    key_pair_name = string

    instance_type    = optional(string, "t3.large")
    launch_type      = optional(string, "FARGATE")
    network_mode     = optional(string, "awsvpc")
    platform_version = optional(string, "LATEST")

    min_size = optional(number, 1)
    max_size = optional(number, 3)

    default_target_group_arn = string

    target_groups = map(object({
      arn = string
    }))

    volumes = optional(list(string), [])

    secrets = optional(list(string), [])

    containers = any
  })

  description = "Cluster config"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "secrets_dir" {
  type = string

  description = "Secrets directory"
}