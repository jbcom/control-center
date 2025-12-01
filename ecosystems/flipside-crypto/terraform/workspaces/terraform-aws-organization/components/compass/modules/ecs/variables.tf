variable "name" {
  type    = string
  default = "compass"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "data_source_encryption_key" {
  type = string
}

# variable "mounted_volume_name" {
#   type    = string
#   default = "query_runs"
# }


# variable "egress_all_sg_id" {
#   type    = string
# }

# variable "ingress_rpc_sg_id" {
#   type    = string
# }

# variable "efs_mount_sg_id" {
#   type    = string
# }

# variable "efs_mount_target_sg_id" {
#   type    = string
# }

# variable "efs_id" {
#   type    = string
# }


# variable "subnets" {
#   type    = list(string)
# }

# variable "rpc_cpu" {
#   type    = string
#   default = 1024
# }

# variable "rpc_memory" {
#   type    = string
#   default = 2048
# }

# variable "rpc_count" {
#   type    = string
#   default = 2
# }

# variable "worker_cpu" {
#   type    = string
#   default = 1024
# }

# variable "worker_memory" {
#   type    = string
#   default = 2048
# }

# variable "worker_count" {
#   type    = string
#   default = 2
# }

# variable "alb_target_group_arn" {
#   type    = string
# }

# variable "database_url" {
#   type    = string
# }

# variable "database_name" {
#   type    = string
#   default = "postgres"
# }

# variable "data_sources_encryption_key" {
#   type    = string
#   default = "gQs5bxdN9HB3AaWeTYGqncX4JP7tjp"
# }

# variable "query_run_results_dir" {
#   type    = string
#   default = "/data"
# }

# variable "ecr_rpc_url" {
#   type    = string
# }

# variable "ecr_rpc_image_tag" {
#   type    = string
# }

# variable "ecr_worker_url" {
#   type    = string
# }

# variable "ecr_worker_image_tag" {
#   type    = string
# }

# variable "rpc_port" {
#   type    = string
#   default = 8000
# }

# variable "firehose_delivery_stream" {
#   type = string
# }

# variable "sentry_dsn_rpc" {
#   type = string
# }

# variable "sentry_dsn_workers" {
#   type = string
# }

# variable "datadog_api_key" {
#   type = string
# }