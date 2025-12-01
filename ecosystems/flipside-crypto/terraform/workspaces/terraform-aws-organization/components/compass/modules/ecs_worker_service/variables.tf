# General
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

# VPC
variable "vpc_name" {
  type = string
}

# Scale
variable "cpu" {
  type    = number
  default = 1024
}

variable "memory" {
  type    = number
  default = 2048
}

variable "service_count" {
  type    = number
  default = 4
}

# Security Groups
variable "sg_egress_all_name" {
  type = string
}

variable "sg_efs_mount_target_name" {
  type = string
}

# ECS Cluster
variable "cluster_name" {
  type = string
}

# ECR
variable "ecr_repository_name" {
  type = string
}

variable "image_tag" {
  type = string
}

# EFS
variable "efs_name" {
  type = string
}

# IAM
variable "iam_task_execution_role_name" {
  type = string
}

# SSM Parameter Store Paths
variable "ssm_arn_app_db_write_url" {
  type = string
}

variable "ssm_arn_access_key_id" {
  type = string
}

variable "ssm_arn_secret_access_key" {
  type = string
}

variable "ssm_arn_data_source_encryption_key" {
  type = string
}

variable "ssm_arn_sentry_dsn_workers" {
  type = string
}

variable "ssm_arn_datadog_api_key" {
  type = string
}

variable "ssm_arn_firehose_delivery_stream" {
  type = string
}

# Query Run Data
variable "query_run_results_dir" {
  type    = string
  default = "/data"
}

variable "mounted_volume_name" {
  type = string
}