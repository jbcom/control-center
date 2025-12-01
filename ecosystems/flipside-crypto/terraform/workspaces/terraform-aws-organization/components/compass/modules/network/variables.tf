/* VPC
*/
variable "vpc_name" {
  type    = string
  default = "vpc"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "vpc_cidr_block" {
  type    = string
  default = "10.0.0.0/16"
}

/* Public Subnets
*/
variable "subnet_a_public_cidr" {
  type    = string
  default = "10.0.1.128/25"
}

variable "subnet_b_public_cidr" {
  type    = string
  default = "10.0.2.128/25"
}

variable "subnet_c_public_cidr" {
  type    = string
  default = "10.0.3.128/25"
}

variable "subnet_d_public_cidr" {
  type    = string
  default = "10.0.4.128/25"
}

variable "subnet_e_public_cidr" {
  type    = string
  default = "10.0.5.128/25"
}


/* Private Subnets
*/
variable "subnet_a_private_cidr" {
  type    = string
  default = "10.0.6.0/25"
}

variable "subnet_b_private_cidr" {
  type    = string
  default = "10.0.7.0/25"
}

variable "subnet_c_private_cidr" {
  type    = string
  default = "10.0.8.0/25"
}

variable "subnet_d_private_cidr" {
  type    = string
  default = "10.0.9.0/25"
}

variable "subnet_e_private_cidr" {
  type    = string
  default = "10.0.10.0/25"
}