variable "ipam_pool_id" {
  type = string

  description = "IPAM pool"
}

variable "cidr_block" {
  type = string

  description = "CIDR block within the IPAM pool"
}

variable "mongodb_aws_region" {
  type = string

  description = "MongoDB AWS region"
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