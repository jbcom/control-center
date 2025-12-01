/* VPC
*/

variable "vpc_name" {
  type = string
}

variable "public_db_subnet_group_name" {
  type = string
}

variable "name" {
  type    = string
  default = "compass"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "instance_class" {
  type    = string
  default = "db.r5.large"
}

# variable "allowed_cidr_blocks" {
#   type    = list(string)
# }