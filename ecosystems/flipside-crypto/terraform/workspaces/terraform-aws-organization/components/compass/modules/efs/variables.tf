variable "efs_name" {
  type    = string
  default = "compass"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "vpc_name" {
  type = string
}

variable "sg_efs_mount_name" {
  type = string
}

# variable "efs_mount_sg_id" {
#   type    = string
# }

# variable "subnet_a_id" {
#   type    = string
# }

# variable "subnet_b_id" {
#   type    = string
# }

# variable "subnet_c_id" {
#   type    = string
# }

# variable "subnet_d_id" {
#   type    = string
# }

# variable "subnet_e_id" {
#   type    = string
# }