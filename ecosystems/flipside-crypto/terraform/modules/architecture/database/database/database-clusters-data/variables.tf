variable "rds_cluster_name" {
  type = string

  description = "RDS cluster name"
}

variable "rds_cluster_environment" {
  type = string

  default = null

  description = "RDS cluster environment"
}

variable "rds_cluster_tags" {
  type = map(string)

  default = {}

  description = "RDS cluster tags"
}

variable "aws_region" {
  type = string

  default = null

  description = "AWS region for tagging the cluster - Defaults to the region active for the Terraform workspace"
}

variable "aws_assumed_role_arn" {
  type = string

  default = ""

  description = "AWS assumed role ARN for tagging the cluster"
}

variable "tag_cluster" {
  type = bool

  default = false

  description = "Whether to tag the cluster or not"
}
