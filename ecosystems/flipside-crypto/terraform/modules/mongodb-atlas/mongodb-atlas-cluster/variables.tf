variable "cluster_id" {
  type = string

  description = "Cluster identifier"
}

variable "mongodb_aws_region" {
  type = string

  description = "MongoDB AWS region"
}

variable "config" {
  type = object({
    cloud_provider = optional(string, "AWS")

    org_id = optional(string, "60db5aee962017151c751b18")

    networks = optional(list(string), [])

    project_name       = optional(string, null)
    cluster_name       = optional(string)
    auth_database_name = optional(string, "admin")
    user_name          = string

    databases = optional(map(string), {})

    cluster_type = optional(string, "REPLICASET")

    instance_type                                   = string
    auto_scaling_compute_scale_down_enabled         = optional(bool, true)
    auto_scaling_compute_enabled                    = optional(bool, true)
    provider_auto_scaling_compute_min_instance_size = optional(string, "M10")
    provider_auto_scaling_compute_max_instance_size = optional(string, "M40")

    disk_size_gb                 = optional(number)
    auto_scaling_disk_gb_enabled = optional(bool, true)
    volume_type                  = optional(string, "STANDARD")
    provider_disk_iops           = optional(number)

    num_shards = optional(number)

    mongodb_major_ver = number

    cloud_backup = optional(bool, true)
    pit_enabled  = optional(bool, false)
  })

  description = "Database config"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "records_dir" {
  type = string

  description = "Records file directory"
}

variable "records_file_name" {
  type = string

  description = "Records file name"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}